"""
services/gds.py - version stream (aucune relation créée en base)
Utilise uniquement PURCHASED et REVIEWED existants.
"""
from config.database import db
import logging
import math

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def projection_exists(name: str) -> bool:
    try:
        result = db.query(
            "CALL gds.graph.exists($name) YIELD exists",
            {"name": name},
        )
        return bool(result[0]["exists"]) if result else False
    except Exception:
        return False


def drop_projection(name: str) -> None:
    try:
        if projection_exists(name):
            db.query("CALL gds.graph.drop($name) YIELD graphName", {"name": name})
            logger.info(f"Projection '{name}' supprimée.")
    except Exception as e:
        logger.warning(f"Impossible de supprimer '{name}': {e}")


def _serialize(result: list) -> dict:
    if not result:
        return {"status": "aucun résultat retourné"}
    row = result[0]
    out = {}
    for k, v in row.items():
        if isinstance(v, float):
            out[k] = None if (math.isnan(v) or math.isinf(v)) else float(v)
        elif isinstance(v, int):
            out[k] = int(v)
        elif v is not None:
            out[k] = str(v)
        else:
            out[k] = None
    return out


def _get_customer_and_product_ids(limit: int = 100) -> tuple[list, list]:
    """
    Calcule une seule fois les IDs Neo4j internes des {limit} premiers clients
    (triés par toInteger pour éviter le tri lexicographique des strings)
    et de tous leurs produits associés via PURCHASED ou REVIEWED.
    """
    id_rows = db.query(
        """
        MATCH (c:Customer)
        RETURN id(c) AS nid
        ORDER BY toInteger(c.client_id)
        LIMIT $limit
        """,
        {"limit": limit}
    )
    customer_ids = [r["nid"] for r in id_rows]

    prod_rows = db.query(
        """
        MATCH (c:Customer)-[:PURCHASED|REVIEWED]->(p:Product)
        WHERE id(c) IN $ids
        RETURN DISTINCT id(p) AS nid
        """,
        {"ids": customer_ids}
    )
    product_ids = [r["nid"] for r in prod_rows]

    logger.info(f"Subset: {len(customer_ids)} clients, {len(product_ids)} produits")
    return customer_ids, product_ids


def get_subset_customer_ids(limit: int = 100) -> list:
    """Récupère les client_id (string) des {limit} premiers clients."""
    rows = db.query(
        """
        MATCH (c:Customer)
        RETURN c.client_id AS cid
        ORDER BY toInteger(c.client_id)
        LIMIT $limit
        """,
        {"limit": limit},
    )
    return [r["cid"] for r in rows]


# ─────────────────────────────────────────────
# PROJECTIONS
# ─────────────────────────────────────────────

def create_global_projection(customer_ids: list, product_ids: list, all_ids: list) -> dict:
    """
    Projection Customer + Product sur le subset.
    Utilisée pour PageRank, Degree, Betweenness et stream similarité clients.
    Gardée active après le pipeline pour les appels stream à la demande.
    """
    name = "global-customer-product"
    drop_projection(name)

    result = db.query(
        """
        CALL gds.graph.project.cypher(
            $name,
            'MATCH (n) WHERE id(n) IN $ids RETURN id(n) AS id',
            'MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
             WHERE id(c) IN $cids AND id(p) IN $pids
             RETURN id(c) AS source, id(p) AS target,
                    coalesce(r.quantity, 1) AS quantity
             UNION ALL
             MATCH (c:Customer)-[r:REVIEWED]->(p:Product)
             WHERE id(c) IN $cids AND id(p) IN $pids
             RETURN id(c) AS source, id(p) AS target,
                    coalesce(r.rating, 1.0) AS quantity',
            {
                parameters: {
                    ids:  $all_ids,
                    cids: $customer_ids,
                    pids: $product_ids
                }
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        """,
        {
            "name":         name,
            "all_ids":      all_ids,
            "customer_ids": customer_ids,
            "product_ids":  product_ids,
        }
    )
    logger.info(f"Projection globale créée : {result}")
    return _serialize(result)


def create_product_projection(customer_ids: list, product_ids: list, all_ids: list) -> dict:
    """
    Projection bipartite Product ← Customer (PURCHASED inversé).
    Gardée active après le pipeline pour les appels stream similarité produits.
    """
    name = "product-customer-bipartite"
    drop_projection(name)

    result = db.query(
        """
        CALL gds.graph.project.cypher(
            $name,
            'MATCH (n) WHERE id(n) IN $ids RETURN id(n) AS id',
            'MATCH (c:Customer)-[:PURCHASED]->(p:Product)
             WHERE id(c) IN $cids AND id(p) IN $pids
             RETURN id(p) AS source, id(c) AS target',
            {
                parameters: {
                    ids:  $all_ids,
                    cids: $customer_ids,
                    pids: $product_ids
                }
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        """,
        {
            "name":         name,
            "all_ids":      all_ids,
            "customer_ids": customer_ids,
            "product_ids":  product_ids,
        }
    )
    logger.info(f"Projection produit créée : {result}")
    return _serialize(result)


# ─────────────────────────────────────────────
# ALGORITHMES — écriture propriétés uniquement
# ─────────────────────────────────────────────

def run_pagerank() -> dict:
    result = db.query(
        """
        CALL gds.pageRank.write('global-customer-product', {
            writeProperty: 'pagerank',
            maxIterations: 20,
            dampingFactor: 0.85
        })
        YIELD nodePropertiesWritten, ranIterations
        """
    )
    logger.info(f"PageRank terminé : {result}")
    return _serialize(result)


def run_degree_centrality() -> dict:
    result = db.query(
        """
        CALL gds.degree.write('global-customer-product', {
            writeProperty: 'degree'
        })
        YIELD nodePropertiesWritten
        """
    )
    logger.info(f"Degree terminé : {result}")
    return _serialize(result)


def run_betweenness() -> dict:
    result = db.query(
        """
        CALL gds.betweenness.write('global-customer-product', {
            writeProperty: 'betweenness',
            samplingSize:  50
        })
        YIELD nodePropertiesWritten
        """
    )
    logger.info(f"Betweenness terminé : {result}")
    return _serialize(result)


# ─────────────────────────────────────────────
# STREAM SIMILARITÉ (aucune relation écrite)
# ─────────────────────────────────────────────
def stream_similar_customers(customer_neo4j_id: int, top_k: int = 10) -> list[dict]:
    result = db.query(
        """
        CALL gds.nodeSimilarity.stream('global-customer-product', {
            similarityCutoff: 0.05,
            topK: $top_k
        })
        YIELD node1, node2, similarity
        WHERE node1 = $nid OR node2 = $nid
        RETURN
            CASE WHEN node1 = $nid THEN node2 ELSE node1 END AS similar_nid,
            similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """,
        {"nid": customer_neo4j_id, "top_k": top_k}
    )
    return result


def stream_similar_products(product_neo4j_id: int, top_k: int = 10) -> list[dict]:
    result = db.query(
        """
        CALL gds.nodeSimilarity.stream('product-customer-bipartite', {
            similarityCutoff: 0.05,
            topK: $top_k
        })
        YIELD node1, node2, similarity
        WHERE node1 = $nid OR node2 = $nid
        RETURN
            CASE WHEN node1 = $nid THEN node2 ELSE node1 END AS similar_nid,
            similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """,
        {"nid": product_neo4j_id, "top_k": top_k}
    )
    return result

# ─────────────────────────────────────────────
# LOUVAIN — segmentation clients
# ─────────────────────────────────────────────

def create_cooccurrence_projection(customer_ids: list, all_ids: list) -> dict:
    """
    Projection client-client via co-achats à la volée.
    Utilisée uniquement pour Louvain.
    """
    name = "customer-cooccurrence"
    drop_projection(name)

    result = db.query(
        """
        CALL gds.graph.project.cypher(
            $name,
            'MATCH (n) WHERE id(n) IN $cids RETURN id(n) AS id',
            'MATCH (c1:Customer)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(c2:Customer)
             WHERE id(c1) IN $cids AND id(c2) IN $cids AND id(c1) < id(c2)
             RETURN id(c1) AS source, id(c2) AS target, count(p) AS weight',
            {
                parameters: {
                    cids: $customer_ids
                }
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        """,
        {
            "name":         name,
            "customer_ids": customer_ids,
        }
    )
    logger.info(f"Projection co-occurrence créée : {result}")
    return _serialize(result)


def run_louvain() -> dict:
    """Louvain — écrit c.community sur chaque Customer du subset."""
    result = db.query(
        """
        CALL gds.louvain.write('customer-cooccurrence', {
            writeProperty: 'community',
            relationshipWeightProperty: 'weight'
        })
        YIELD communityCount, modularity, nodePropertiesWritten
        """
    )
    logger.info(f"Louvain terminé : {result}")
    return _serialize(result)

# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────
def run_all_algorithms(limit: int = 10000) -> dict:
    report = {}
    logger.info(f"=== Démarrage pipeline GDS — limit={limit} ===")

    try:
        customer_ids, product_ids = _get_customer_and_product_ids(limit)
        all_ids = customer_ids + product_ids

        # 1. Louvain — segmentation clients (projection séparée)
        report["cooccurrence_projection"] = create_cooccurrence_projection(customer_ids, all_ids)
        report["louvain"]                 = run_louvain()
        drop_projection("customer-cooccurrence")

        # 2. Projection globale + centralités
        report["global_projection"] = create_global_projection(customer_ids, product_ids, all_ids)
        report["pagerank"]          = run_pagerank()
        report["degree"]            = run_degree_centrality()
        report["betweenness"]       = run_betweenness()

        # 3. Projection produits (gardée active pour stream)
        report["product_projection"] = create_product_projection(customer_ids, product_ids, all_ids)

    except Exception as e:
        logger.error(f"Pipeline GDS FAILED: {e}")
        drop_projection("customer-cooccurrence")
        drop_projection("global-customer-product")
        drop_projection("product-customer-bipartite")
        raise

    logger.info("=== Pipeline GDS terminé ===")
    return report