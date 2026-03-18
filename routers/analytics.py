"""
routers/analytics.py
Endpoints d'analyse globale : catégories, revenus, stats graphe.
"""
from fastapi import APIRouter
from services.recommendation import get_category_insights
from config.database import db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/categories")
def category_insights():
    """
    Analyse par catégorie : achats, quantité, revenue, note moyenne.
    """
    results = get_category_insights()
    return {"count": len(results), "categories": results}


@router.get("/graph-stats")
def graph_stats():
    """
    Statistiques globales du graphe Neo4j.
    """
    stats = {}

    counts = db.query("""
        MATCH (c:Customer) WITH count(c) AS customers
        MATCH (p:Product)  WITH customers, count(p) AS products
        RETURN customers, products
    """)
    if counts:
        stats.update(counts[0])

    rels = db.query("""
        MATCH ()-[r:PURCHASED]->() WITH count(r) AS purchases
        MATCH ()-[r2:REVIEWED]->() WITH purchases, count(r2) AS reviews
        OPTIONAL MATCH ()-[r3:SIMILAR_TO]->()
        RETURN purchases, reviews, count(r3) AS similarity_relations
    """)
    if rels:
        stats.update(rels[0])

    algo_check = db.query("""
        MATCH (p:Product) WHERE p.pagerank IS NOT NULL
        RETURN count(p) AS products_with_pagerank
    """)
    if algo_check:
        stats["algorithms_computed"] = algo_check[0]["products_with_pagerank"] > 0

    return {"graph_stats": stats}
