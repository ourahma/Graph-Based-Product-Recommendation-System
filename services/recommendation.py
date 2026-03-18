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

def recommend_for_client(client_id: str, top_k: int = 5) -> list[dict]:
    """
    Collaborative Filtering via stream GDS (rien écrit en base).
    Score = 0.70 * cf_score + 0.30 * pagerank_score
    """
    # 1. Récupérer le neo4j id() interne du client
    row = db.query(
        "MATCH (c:Customer {client_id: $cid}) RETURN id(c) AS nid",
        {"cid": client_id}
    )
    if not row:
        logger.warning(f"Client '{client_id}' introuvable")
        return []
    nid = row[0]["nid"]

    # 2. Produits déjà achetés (par id interne pour éviter pb de type)
    bought = db.query(
        """
        MATCH (c:Customer {client_id: $cid})-[:PURCHASED]->(p:Product)
        RETURN id(p) AS nid
        """,
        {"cid": client_id}
    )
    already_ids = [r["nid"] for r in bought]

    # 3. Clients similaires via stream GDS (aucune relation créée)
    similar_customers = stream_similar_customers(nid, top_k=20)
    if not similar_customers:
        logger.warning(f"Aucun client similaire trouvé pour '{client_id}'")
        return []

    similar_nids = [r["similar_nid"] for r in similar_customers]
    sim_map = {r["similar_nid"]: r["similarity"] for r in similar_customers}

    # 4. Produits achetés par ces clients similaires, non encore achetés
    candidates = db.query(
        """
        MATCH (c)-[r:PURCHASED]->(p:Product)
        WHERE id(c) IN $nids
          AND NOT id(p) IN $already_ids
        RETURN
            id(p)            AS product_nid,
            p.product_id     AS product_id,
            p.product_name   AS product_name,
            p.category       AS category,
            p.brand          AS brand,
            p.price          AS price,
            coalesce(p.pagerank, 0.0) AS pagerank,
            id(c)            AS customer_nid,
            coalesce(r.quantity, 1.0) AS quantity
        """,
        {"nids": similar_nids, "already_ids": already_ids}
    )

    # 5. Calcul du score CF agrégé par produit
    scores = {}
    for r in candidates:
        pid = r["product_nid"]
        sim = sim_map.get(r["customer_nid"], 0.0)
        if pid not in scores:
            scores[pid] = {"row": r, "raw_cf": 0.0, "supporters": 0}
        scores[pid]["raw_cf"] += sim * r["quantity"]
        scores[pid]["supporters"] += sim
    # 6. Score final
    results = []
    for pid, data in scores.items():
        r        = data["row"]
        cf_score = data["raw_cf"] / (1e-6 + data["supporters"])
        cf_score = cf_score / (1 + cf_score)
        pr       = r["pagerank"]
        pr_score = pr / (1.0 + pr)
        
        final    = round(0.70 * cf_score + 0.30 * pr_score, 4)
        results.append({
            "product_id":      r["product_id"],
            "product_name":    r["product_name"],
            "category":        r["category"],
            "brand":           r["brand"],
            "price":           r["price"],
            "score":           final,
            "method":          "collaborative_filtering",
            "cf_score":        round(cf_score, 4),
            "pagerank_score":  round(pr_score, 4),
            "supporter_count": round(data["supporters"], 4),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"recommend_for_client({client_id}): {len(results[:top_k])} résultats")
    return _clean(results[:top_k])


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
    WITH segment_id,
         size(members) AS size,
         [m IN members | m.country] AS countries,
         [m IN members | m.gender]  AS genders
    RETURN
        segment_id,
        size,
        countries[0..5] AS sample_countries,
        genders[0..5]   AS sample_genders
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
    MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
    WITH p.category                                                            AS category,
         count(r)                                                              AS total_purchases,
         sum(coalesce(r.quantity, 1))                                         AS total_quantity,
         sum(coalesce(r.price_at_purchase, p.price, 0) * coalesce(r.quantity, 1)) AS total_revenue
    OPTIONAL MATCH (:Customer)-[rev:REVIEWED]->(p2:Product)
    WHERE p2.category = category
    RETURN
        category,
        total_purchases,
        total_quantity,
        round(total_revenue, 2)   AS total_revenue,
        round(avg(rev.rating), 2) AS avg_rating,
        count(rev)                AS total_reviews
    ORDER BY total_revenue DESC
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