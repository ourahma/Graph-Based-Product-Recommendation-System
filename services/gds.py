from config.database import db
import logging
import math
from typing import Any, Dict

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


def _serialize(result: list) -> Dict[str, Any]:
    if not result:
        return {"status": "aucun résultat retourné"}
    row = result[0]
    out: Dict[str, Any] = {}
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

def create_global_projection(customer_ids: list, product_ids: list, all_ids: list) -> Dict[str, Any]:
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


def create_product_projection(customer_ids: list, product_ids: list, all_ids: list) -> Dict[str, Any]:
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
# ALGORITHMES 
# ─────────────────────────────────────────────

def run_pagerank() -> Dict[str, Any]:
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


def run_degree_centrality() -> Dict[str, Any]:
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


def run_betweenness() -> Dict[str, Any]:
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
# STREAM SIMILARITÉ 
# ─────────────────────────────────────────────
def stream_similar_customers(customer_neo4j_id: int, top_k: int = 10) -> list[dict]:
    try:
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
    except Exception as e:
        error_msg = str(e)
        if "GraphNotFoundException" in error_msg or "does not exist" in error_msg:
            logger.error(
                f"Graph 'global-customer-product' not found! "
                f"The pipeline may need to be re-run. Error: {error_msg}"
            )
        else:
            logger.error(f"Error streaming similar customers: {error_msg}")
        raise


def stream_similar_products(product_neo4j_id: int, top_k: int = 10) -> list[dict]:
    try:
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
    except Exception as e:
        error_msg = str(e)
        if "GraphNotFoundException" in error_msg or "does not exist" in error_msg:
            logger.error(
                f"Graph 'product-customer-bipartite' not found! "
                f"The pipeline may need to be re-run. Error: {error_msg}"
            )
        else:
            logger.error(f"Error streaming similar products: {error_msg}")
        raise

# ─────────────────────────────────────────────
# LOUVAIN — segmentation clients
# ─────────────────────────────────────────────

def create_cooccurrence_projection(customer_ids: list, all_ids: list) -> Dict[str, Any]:
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


def run_louvain() -> Dict[str, Any]:
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
def run_all_algorithms(limit: int = 10000) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
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


# ─────────────────────────────────────────────
# DIAGNOSTIQUE
# ─────────────────────────────────────────────

def diagnose_customer(client_id: str) -> Dict[str, Any]:
    """
    Diagnostic pour un client spécifique.
    """
    # Initialisation avec annotation explicite pour éviter l'inférence Dict[str, str]
    info: Dict[str, Any] = {}
    info["client_id"] = client_id
    
    # 1. Client exists?
    row = db.query(
        "MATCH (c:Customer {client_id: $cid}) RETURN id(c) AS nid, c.name AS name, c.community AS community",
        {"cid": client_id}
    )
    if not row:
        info["exists"] = False 
        info["error"] = f"Client '{client_id}' n'existe pas dans la base"
        return info
    
    nid = row[0]["nid"]
    info["exists"] = True
    info["neo4j_id"] = nid
    info["name"] = row[0].get("name", "N/A")
    info["community"] = row[0].get("community", "N/A")
    
    # 2. Purchases count
    purchases = db.query(
        "MATCH (c:Customer {client_id: $cid})-[:PURCHASED]->(p:Product) RETURN count(p) AS count",
        {"cid": client_id}
    )
    info["purchase_count"] = purchases[0]["count"] if purchases else 0
    
    # 3. In graph projection?
    try:
        exists_check = db.query(
            "CALL gds.graph.exists('global-customer-product') YIELD exists",
        )
        graph_exists = exists_check[0]["exists"] if exists_check else False
        info["graph_global_customer_product_exists"] = graph_exists
        
        if graph_exists:
            result = db.query(
                "CALL gds.nodeSimilarity.stream('global-customer-product', {similarityCutoff: 0.0, topK: 1}) "
                "YIELD node1, node2, similarity WHERE node1 = $nid RETURN count(*) AS count",
                {"nid": nid}
            )
            in_projection = result and result[0]["count"] > 0 if result else False
            info["in_global_projection"] = in_projection
        else:
            info["in_global_projection"] = "N/A - graph not loaded"
    except Exception as e:
        info["in_global_projection"] = f"Erreur: {str(e)}"
    
    # 4. Similarity scores stats
    try:
        exists_check = db.query(
            "CALL gds.graph.exists('global-customer-product') YIELD exists",
        )
        if exists_check and exists_check[0]["exists"]:
            similarities = db.query(
                "CALL gds.nodeSimilarity.stream('global-customer-product', {similarityCutoff: 0.0, topK: 100}) "
                "YIELD node1, node2, similarity WHERE node1 = $nid OR node2 = $nid "
                "RETURN count(*) AS total, min(similarity) AS min_sim, max(similarity) AS max_sim, "
                "avg(similarity) AS avg_sim",
                {"nid": nid}
            )
            if similarities and similarities[0]["total"] > 0:
                info["similarity_stats"] = {
                    "total": similarities[0]["total"],
                    "min": round(similarities[0]["min_sim"], 4),
                    "max": round(similarities[0]["max_sim"], 4),
                    "avg": round(similarities[0]["avg_sim"], 4),
                }
            else:
                info["similarity_stats"] = "Aucune similarité trouvée (même avec threshold 0.0)"
        else:
            info["similarity_stats"] = "N/A - graph not loaded"
    except Exception as e:
        info["similarity_stats"] = f"Erreur: {str(e)}"
    
    return info


def list_all_clients(limit: int = 20) -> list[dict]:
    """
    Liste des premiers clients avec leurs stats.
    """
    rows = db.query(
        """
        MATCH (c:Customer)
        RETURN c.client_id AS client_id, c.name AS name, 
               COUNT { (c)-[:PURCHASED]->() } AS purchases
        ORDER BY toInteger(c.client_id)
        LIMIT $limit
        """,
        {"limit": limit}
    )
    return rows


def diagnose_duplicates() -> Dict[str, Any]:
    """
    Diagnostic des doublons de customers dans la base.
    Vérifie si chaque client_id a une seule node ou plusieurs.
    """
    result = db.query(
        """
        MATCH (c:Customer)
        WITH c.client_id AS cid, count(c) AS node_count
        WHERE node_count > 1
        RETURN cid, node_count
        ORDER BY node_count DESC
        LIMIT 20
        """
    )
    
    if not result:
        return {"duplicates_found": False, "message": "Aucun doublon détecté"}
    
    return {
        "duplicates_found": True,
        "duplicate_count": len(result),
        "duplicates": result
    }


def customer_stats() -> Dict[str, Any]:
    """
    Statistiques globales sur les customers et les purchases.
    """
    stats: Dict[str, Any] = {}
    
    # Total unique customer_ids
    try:
        unique = db.query("""
            MATCH (c:Customer)
            RETURN COUNT(DISTINCT c.client_id) AS count
        """)
        stats["unique_customer_ids"] = unique[0]["count"] if unique else 0
    except Exception as e:
        logger.warning(f"Error counting unique customer ids: {e}")
        stats["unique_customer_ids"] = 0
    
    # Total customer nodes
    try:
        total = db.query("""
            MATCH (c:Customer)
            RETURN COUNT(c) AS count
        """)
        stats["total_customer_nodes"] = total[0]["count"] if total else 0
    except Exception as e:
        logger.warning(f"Error counting total customer nodes: {e}")
        stats["total_customer_nodes"] = 0
    
    # Customers with purchases
    try:
        with_purchases = db.query("""
            MATCH (c:Customer)-[:PURCHASED]->()
            RETURN COUNT(DISTINCT c.client_id) AS count
        """)
        stats["customers_with_purchases"] = with_purchases[0]["count"] if with_purchases else 0
    except Exception as e:
        logger.warning(f"Error counting customers with purchases: {e}")
        stats["customers_with_purchases"] = 0
    
    # Total purchases
    try:
        purchase_count = db.query("""
            MATCH ()-[:PURCHASED]->()
            RETURN COUNT(*) AS count
        """)
        stats["total_purchases"] = purchase_count[0]["count"] if purchase_count else 0
    except Exception as e:
        logger.warning(f"Error counting total purchases: {e}")
        stats["total_purchases"] = 0
    
    return stats


def list_all_products(limit: int = 100) -> list[dict]:
    """
    Liste des produits avec leurs statistiques.
    """
    rows = db.query(
        """
        MATCH (p:Product)
        RETURN p.product_id AS product_id, p.product_name AS product_name, 
               p.category AS category, p.price AS price,
               COUNT { (p)<-[:PURCHASED]-() } AS purchase_count,
               COUNT { (p)<-[:REVIEWED]-() } AS review_count
        ORDER BY purchase_count DESC
        LIMIT $limit
        """,
        {"limit": limit}
    )
    return rows


def pipeline_graph_info() -> Dict[str, Any]:
    """
    Info sur les projections GDS actuellement actives.
    """
    info: Dict[str, Any] = {}
    
    for graph_name in ["global-customer-product", "product-customer-bipartite"]:
        try:
            # Check if graph exists
            exists_result = db.query(
                "CALL gds.graph.exists($name) YIELD exists",
                {"name": graph_name}
            )
            exists = exists_result[0]["exists"] if exists_result else False
            
            if not exists:
                info[graph_name] = {"exists": False}
            else:
                # Get graph info
                graph_info = db.query(
                    "CALL gds.graph.list($name) YIELD graphName, nodeCount, relationshipCount",
                    {"name": graph_name}
                )
                if graph_info:
                    info[graph_name] = {
                        "exists": True,
                        "nodeCount": graph_info[0]["nodeCount"],
                        "relationshipCount": graph_info[0]["relationshipCount"],
                    }
                else:
                    info[graph_name] = {"exists": False}
        except Exception as e:
            info[graph_name] = {"exists": False, "error": str(e)}
    
    return info