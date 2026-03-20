"""
services/recommendation.py
"""
from config.database import db
from services.gds import stream_similar_customers, stream_similar_products
from utils.cache import timed_cache
import logging
import math

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# UTILITAIRE
# ─────────────────────────────────────────────────────────────────

def _clean(rows: list) -> list[dict]:
    cleaned = []
    for row in rows:
        record = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                record[k] = None
            else:
                record[k] = v
        cleaned.append(record)
    return cleaned


# ─────────────────────────────────────────────────────────────────
# RECOMMANDATION POUR UN CLIENT
# ─────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional

def recommend_for_client(client_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Collaborative Filtering via stream GDS (rien écrit en base).
    Score = 0.70 * cf_score + 0.30 * pagerank_score
    
    Args:
        client_id: L'ID métier du client (propriété `client_id` sur le nœud Customer)
        top_k: Nombre de recommandations à retourner
    
    Returns:
        List[Dict[str, Any]]: Liste des produits recommandés avec scores détaillés
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # ─────────────────────────────────────────
    # 1. Récupérer le client (matching flexible client_id)
    # ─────────────────────────────────────────
    # On utilise toString() pour gérer les cas où client_id est stocké en int vs reçu en string
    row = db.query(
        """
        MATCH (c:Customer) 
        WHERE toString(c.client_id) = toString($cid)
        RETURN id(c) AS nid, c.name AS name, c.pagerank AS pr, c.client_id AS actual_cid
        LIMIT 1
        """,
        {"cid": client_id}
    )
    
    if not row:
        logger.warning(f"Client avec client_id='{client_id}' introuvable dans la base")
        return _fallback_recommendations(top_k, reason=f"client '{client_id}' non trouvé")
    
    nid = row[0]["nid"]
    actual_cid = row[0]["actual_cid"]  # L'ID tel qu'il est stocké en base
    client_name = row[0].get("name", "N/A")
    client_pagerank = row[0].get("pr")
    
    logger.info(f"Client trouvé : client_id='{client_id}' (stocké: '{actual_cid}'), nid={nid}, pagerank={client_pagerank}")

    # ─────────────────────────────────────────
    # 2. Vérifier que la projection GDS existe
    # ─────────────────────────────────────────
    try:
        graph_check = db.query(
            "CALL gds.graph.exists('global-customer-product') YIELD exists",
        )
        if not graph_check or not graph_check[0]["exists"]:
            logger.error("Projection 'global-customer-product' non trouvée ! Relancez le pipeline GDS.")
            return _fallback_recommendations(top_k, reason="projection GDS manquante")
    except Exception as e:
        logger.error(f"Erreur vérification projection GDS: {e}")
        return _fallback_recommendations(top_k, reason=f"erreur projection: {e}")

    # ─────────────────────────────────────────
    # 3. Produits déjà achetés par ce client (IDs internes Neo4j)
    # ─────────────────────────────────────────
    bought = db.query(
        """
        MATCH (c:Customer)-[:PURCHASED]->(p:Product)
        WHERE toString(c.client_id) = toString($cid)
        RETURN id(p) AS nid
        """,
        {"cid": client_id}
    )
    already_ids: List[int] = [r["nid"] for r in bought]
    logger.info(f"Client '{actual_cid}' a déjà acheté {len(already_ids)} produits")

    # ─────────────────────────────────────────
    # 4. Clients similaires via GDS Node Similarity
    # ─────────────────────────────────────────
    similar_customers = stream_similar_customers(nid, top_k=20)
    
    if not similar_customers:
        # 🔍 Debug avec cutoff=0.0 pour diagnostiquer
        logger.warning(f"Aucun client similaire trouvé pour '{actual_cid}' avec cutoff=0.05")
        
        try:
            debug_result = db.query(
                """
                CALL gds.nodeSimilarity.stream('global-customer-product', {
                    similarityCutoff: 0.0,
                    topK: 5
                })
                YIELD node1, node2, similarity
                WHERE node1 = $nid OR node2 = $nid
                RETURN count(*) AS count, min(similarity) AS min_sim, max(similarity) AS max_sim
                """,
                {"nid": nid}
            )
            
            if debug_result and debug_result[0]["count"] > 0:
                logger.warning(
                    f"Similarités trouvées avec cutoff=0.0 : count={debug_result[0]['count']}, "
                    f"min={debug_result[0]['min_sim']:.4f}, max={debug_result[0]['max_sim']:.4f}. "
                    f"→ Le seuil 0.05 est probablement trop élevé."
                )
            else:
                logger.warning(
                    f"Client nid={nid} n'a aucune similarité calculée. "
                    f"Vérifiez qu'il fait partie du subset GDS (limit utilisé lors du pipeline)."
                )
        except Exception as e:
            logger.error(f"Erreur debug similarité: {e}")
        
        # Fallback si pas de similarités
        return _fallback_recommendations(top_k, reason="aucun client similaire trouvé", client_nid=nid)
    
    logger.info(f"✓ Trouvé {len(similar_customers)} clients similaires pour '{actual_cid}'")

    # ─────────────────────────────────────────
    # 5. Extraire les produits candidats (achetés par les similaires, pas par le client)
    # ─────────────────────────────────────────
    similar_nids = [r["similar_nid"] for r in similar_customers]
    sim_map = {r["similar_nid"]: r["similarity"] for r in similar_customers}

    candidates = db.query(
        """
        MATCH (c)-[r:PURCHASED]->(p:Product)
        WHERE id(c) IN $nids
          AND NOT id(p) IN $already_ids
        RETURN
            id(p)                     AS product_nid,
            p.product_id              AS product_id,
            p.product_name            AS product_name,
            p.category                AS category,
            p.brand                   AS brand,
            p.price                   AS price,
            coalesce(p.pagerank, 0.0) AS pagerank,
            id(c)                     AS customer_nid,
            coalesce(r.quantity, 1.0) AS quantity
        """,
        {"nids": similar_nids, "already_ids": already_ids}
    )

    if not candidates:
        logger.warning(f"Aucun produit candidat trouvé pour les clients similaires de '{actual_cid}'")
        return _fallback_recommendations(top_k, reason="aucun produit candidat", client_nid=nid)

    # ─────────────────────────────────────────
    # 6. Calcul du score CF agrégé par produit
    # ─────────────────────────────────────────
    scores: Dict[int, Dict[str, Any]] = {}
    
    for r in candidates:
        pid = r["product_nid"]
        sim = sim_map.get(r["customer_nid"], 0.0)
        
        if pid not in scores:
            scores[pid] = {"row": r, "raw_cf": 0.0, "supporters": 0.0}
        
        scores[pid]["raw_cf"] += sim * r["quantity"]
        scores[pid]["supporters"] += sim

    # ─────────────────────────────────────────
    # 7. Score final hybride : 70% CF + 30% PageRank
    # ─────────────────────────────────────────
    results: List[Dict[str, Any]] = []
    
    for pid, data in scores.items():
        r = data["row"]
        
        # Normalisation du score CF
        cf_score = data["raw_cf"] / (1e-6 + data["supporters"])
        cf_score = cf_score / (1 + cf_score)  # Compression [0, 1]
        
        # Normalisation du PageRank
        pr = r["pagerank"] or 0.0
        pr_score = pr / (1.0 + pr)
        
        # Score hybride
        final_score = round(0.70 * cf_score + 0.30 * pr_score, 4)
        
        results.append({
            "product_id":      r["product_id"],
            "product_name":    r["product_name"],
            "category":        r["category"],
            "brand":           r["brand"],
            "price":           float(r["price"]) if r["price"] is not None else None,
            "score":           final_score,
            "method":          "collaborative_filtering",
            "cf_score":        round(cf_score, 4),
            "pagerank_score":  round(pr_score, 4),
            "supporter_count": round(data["supporters"], 4),
        })

    # Tri et retour des top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"✓ recommend_for_client('{actual_cid}'): {len(results[:top_k])} résultats retournés")
    
    return _clean(results[:top_k])


# ─────────────────────────────────────────
# FONCTION FALLBACK (recommandation de secours)
# ─────────────────────────────────────────
def _fallback_recommendations(
    top_k: int, 
    reason: str, 
    client_nid: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fallback : retourne les produits les plus populaires par PageRank
    quand le collaborative filtering échoue.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Fallback activé (raison: {reason}) — récupération des produits populaires")
    
    # Si on connaît le client, on exclut ses achats même en fallback
    exclude_clause = "AND NOT id(p) IN $already" if client_nid else ""
    
    # ✅ Annotation explicite pour éviter l'inférence Dict[str, int]
    exclude_params: Dict[str, Any] = {"limit": top_k}
    
    if client_nid:
        # Récupérer les produits déjà achetés par ce client
        already = db.query(
            """
            MATCH (c)-[:PURCHASED]->(p:Product)
            WHERE id(c) = $nid
            RETURN id(p) AS nid
            """,
            {"nid": client_nid}
        )
        exclude_params["already"] = [r["nid"] for r in already]
    
    results = db.query(
        f"""
        MATCH (p:Product)
        WHERE p.pagerank IS NOT NULL 
        {exclude_clause}
        RETURN 
            p.product_id              AS product_id,
            p.product_name            AS product_name,
            p.category                AS category,
            p.brand                   AS brand,
            p.price                   AS price,
            p.pagerank                AS pagerank
        ORDER BY p.pagerank DESC
        LIMIT $limit
        """,
        exclude_params
    )
    
    fallback_results = []
    for r in results:
        pr = r["pagerank"] or 0.0
        pr_score = pr / (1.0 + pr)
        
        fallback_results.append({
            "product_id":      r["product_id"],
            "product_name":    r["product_name"],
            "category":        r["category"],
            "brand":           r["brand"],
            "price":           float(r["price"]) if r["price"] is not None else None,
            "score":           round(pr_score, 4),
            "method":          "fallback_pagerank",
            "note":            f"Recommandation de secours : {reason}",
        })
    
    logger.info(f"Fallback : {len(fallback_results)} produits retournés")
    return _clean(fallback_results)


# ─────────────────────────────────────────────────────────────────
# RECOMMANDATION POUR UN PRODUIT
# ─────────────────────────────────────────────────────────────────

def recommend_for_product(product_id: str, top_k: int = 5) -> list[dict]:
    """
    Recommandation item-based propre :
    - Similarité via GDS (NodeSimilarity)
    - + léger boost de popularité (degree)
    
    Score final = 0.8 * similarity_norm + 0.2 * popularity_norm
    """

    # 1. Récupérer ID interne
    row = db.query(
        "MATCH (p:Product {product_id: $pid}) RETURN id(p) AS nid",
        {"pid": product_id}
    )
    if not row:
        logger.warning(f"Produit '{product_id}' introuvable")
        return []
    nid = row[0]["nid"]

    # 2. Produits similaires via GDS
    similar = stream_similar_products(nid, top_k=top_k * 3)

    if not similar:
        logger.warning(f"Aucun produit similaire pour '{product_id}', fallback popularité")

        # fallback : produits populaires
        rows = db.query(
            """
            MATCH (p:Product)
            RETURN
                p.product_id    AS product_id,
                p.product_name  AS product_name,
                p.category      AS category,
                p.brand         AS brand,
                p.price         AS price,
                coalesce(p.degree, 0) AS popularity
            ORDER BY popularity DESC
            LIMIT $top_k
            """,
            {"top_k": top_k}
        )

        # normalisation simple
        results = []
        for r in rows:
            pop = r["popularity"]
            pop_score = pop / (1 + pop)

            results.append({
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "category": r["category"],
                "brand": r["brand"],
                "price": r["price"],
                "score": round(pop_score, 4),
                "similarity_score": 0.0,
                "popularity_score": round(pop_score, 4),
            })

        return _clean(results)

    similar_nids = [r["similar_nid"] for r in similar]
    sim_map = {r["similar_nid"]: r["similarity"] for r in similar}

    # 3. Récupérer infos produit + popularité
    candidates = db.query(
        """
        MATCH (p:Product)
        WHERE id(p) IN $nids
        RETURN
            id(p)           AS nid,
            p.product_id    AS product_id,
            p.product_name  AS product_name,
            p.category      AS category,
            p.brand         AS brand,
            p.price         AS price,
            coalesce(p.degree, 0) AS degree
        """,
        {"nids": similar_nids}
    )

    results = []

    for r in candidates:
        sim = sim_map.get(r["nid"], 0.0)

        # normalisation similarité
        sim_norm = sim / (1 + sim)

        # popularité (degree)
        deg = r["degree"]
        pop_norm = deg / (1 + deg)

        # score final
        final = round(0.8 * sim_norm + 0.2 * pop_norm, 4)

        results.append({
            "product_id":        r["product_id"],
            "product_name":      r["product_name"],
            "category":          r["category"],
            "brand":             r["brand"],
            "price":             r["price"],
            "score":             final,
            "similarity_score":  round(sim_norm, 4),
            "popularity_score":  round(pop_norm, 4),
        })

    # 4. Tri
    results.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"recommend_for_product({product_id}): {len(results[:top_k])} résultats")

    return _clean(results[:top_k])

# ─────────────────────────────────────────────────────────────────
# TOP PRODUITS
# ─────────────────────────────────────────────────────────────────

@timed_cache(ttl=300)
def get_top_products(
    method: str = "pagerank",
    limit: int = 50,
    category: str | None = None,
    brand: str | None = None,
) -> list[dict]:
    filters = ["p.pagerank IS NOT NULL"]
    params: dict = {"limit": limit}

    if category:
        filters.append("p.category = $category")
        params["category"] = category
    if brand:
        filters.append("p.brand = $brand")
        params["brand"] = brand

    where_clause = "WHERE " + " AND ".join(filters)

    score_expr = {
        "pagerank":    "coalesce(p.pagerank, 0.0)",
        "degree":      "coalesce(p.degree, 0.0)",
        "betweenness": "coalesce(p.betweenness, 0.0)",
        "combined": """
        0.50 * (coalesce(p.pagerank, 0.0) / (1.0 + coalesce(p.pagerank, 0.0))) +
        0.30 * (coalesce(p.degree, 0.0) / (1.0 + coalesce(p.degree, 0.0))) +
        0.20 * (coalesce(p.betweenness, 0.0) / (1.0 + coalesce(p.betweenness, 0.0)))
        """,
    }.get(method, "coalesce(p.pagerank, 0.0)")

    cypher = f"""
    MATCH (p:Product)
    {where_clause}
    RETURN
        p.product_id     AS product_id,
        p.product_name   AS product_name,
        p.category       AS category,
        p.brand          AS brand,
        p.price          AS price,
        p.stock_quantity AS stock_quantity,
        round(coalesce(p.pagerank,    0.0), 4) AS pagerank,
        round(coalesce(p.degree,      0.0), 4) AS degree,
        round(coalesce(p.betweenness, 0.0), 4) AS betweenness,
        round({score_expr}, 4)                 AS score
    ORDER BY score DESC
    LIMIT $limit
    """
    results = db.query(cypher, params)
    logger.info(f"get_top_products(method={method}): {len(results)} résultats")
    return _clean(results)


# ─────────────────────────────────────────────────────────────────
# SEGMENTS CLIENTS (Louvain)
# ─────────────────────────────────────────────────────────────────

@timed_cache(ttl=300)
def get_segments(limit: int = 20) -> list[dict]:
    cypher = """
    MATCH (c:Customer)
    WHERE c.community IS NOT NULL
    WITH c.community AS segment_id, collect(c) AS members
    RETURN
        segment_id,
        size(members) AS size,
        [m IN members | m.country][0..5] AS sample_countries,
        [m IN members | COALESCE(m.gender, m.Gender, m.sex, 'N/A')][0..5] AS sample_genders
    ORDER BY size DESC
    LIMIT $limit
    """
    results = db.query(cypher, {"limit": limit})
    logger.info(f"get_segments(): {len(results)} segments")
    return _clean(results)


def get_segment_customers(segment_id: int, limit: int = 20) -> list[dict]:
    cypher = """
    MATCH (c:Customer)
    WHERE c.community = $segment_id
    OPTIONAL MATCH (c)-[r:PURCHASED]->(p:Product)
    WITH c,
         count(p)                           AS purchase_count,
         collect(DISTINCT p.category)[0..3] AS fav_categories
    RETURN
        c.client_id AS client_id,
        c.name      AS name,
        c.country   AS country,
        c.gender    AS gender,
        purchase_count,
        fav_categories
    ORDER BY purchase_count DESC
    LIMIT $limit
    """
    return _clean(db.query(cypher, {"segment_id": segment_id, "limit": limit}))


# ─────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────

@timed_cache(ttl=300)
def get_category_insights() -> list[dict]:
    cypher = """
    MATCH (p:Product)
    WITH p.category AS category
    OPTIONAL MATCH (c:Customer)-[r:PURCHASED]->(p2:Product)
    WHERE p2.category = category
    OPTIONAL MATCH ()-[rev:REVIEWED]->(p2)
    WITH category, p2, r, rev
    RETURN
        category,
        COUNT(DISTINCT p2) AS product_count,
        COUNT(r) AS purchase_count,
        ROUND(SUM(COALESCE(r.quantity, 1) * COALESCE(p2.price, 0)), 2) AS total_revenue,
        ROUND(COALESCE(AVG(rev.rating), 4.5), 2) AS avg_rating
    ORDER BY purchase_count DESC
    """
    return _clean(db.query(cypher))


@timed_cache(ttl=300)
def get_top_customers(limit: int = 20) -> list[dict]:
    cypher = """
    MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
    WITH c,
         count(r)                                                              AS order_count,
         sum(coalesce(r.price_at_purchase, p.price, 0) * coalesce(r.quantity, 1)) AS total_spent,
         collect(DISTINCT p.category)[0..3]                                   AS fav_categories
    RETURN
        c.client_id AS client_id,
        c.name      AS name,
        c.country   AS country,
        c.community AS segment,
        order_count,
        round(total_spent, 2) AS total_spent,
        fav_categories
    ORDER BY total_spent DESC
    LIMIT $limit
    """
    return _clean(db.query(cypher, {"limit": limit}))