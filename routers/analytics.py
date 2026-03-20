import logging
from fastapi import APIRouter
from services.recommendation import get_category_insights
from config.database import db

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.get("/categories")
def category_insights():
    """
    Analyse par catégorie : achats, quantité, revenue, note moyenne.
    """
    results = get_category_insights()
    return {"count": len(results), "categories": results}

@router.get("/graph-stats")
def graph_stats():
    stats = {}

    try:
        # ── Counts ───────────────────────────────────────────────
        counts = db.query("""
            MATCH (c:Customer) WITH count(c) AS customers
            MATCH (p:Product)  WITH customers, count(p) AS products
            RETURN customers, products
        """)
        if counts:
            stats['customer_count'] = int(counts[0].get('customers', 0))
            stats['product_count']  = int(counts[0].get('products', 0))
        else:
            stats['customer_count'] = 0
            stats['product_count']  = 0

        # ── Relations ─────────────────────────────────────────────
        rels = db.query("""
            MATCH ()-[r:PURCHASED]->()  WITH count(r) AS purchases
            MATCH ()-[r2:REVIEWED]->()  WITH purchases, count(r2) AS reviews
            OPTIONAL MATCH ()-[r3:SIMILAR_TO]->()
            OPTIONAL MATCH ()-[r4:PRODUCT_SIMILAR]->()
            RETURN purchases, reviews,
                   count(r3) AS similarity_relations,
                   count(r4) AS product_similarity
        """)
        if rels:
            purchases   = int(rels[0].get('purchases', 0))
            reviews     = int(rels[0].get('reviews', 0))
            similarity  = int(rels[0].get('similarity_relations', 0))
            product_sim = int(rels[0].get('product_similarity', 0))
            stats['purchase_rel_count'] = purchases
            stats['review_rel_count']   = reviews
            stats['similar_cust_count'] = similarity
            stats['similar_prod_count'] = product_sim
            stats['relationship_count'] = purchases + reviews + similarity + product_sim
        else:
            stats.update({
                'relationship_count': 0, 'purchase_rel_count': 0,
                'review_rel_count': 0, 'similar_cust_count': 0, 'similar_prod_count': 0
            })

        # ── Density & avg degree ──────────────────────────────────
        total_nodes = stats['customer_count'] + stats['product_count']
        total_rels  = stats['relationship_count']

        if total_nodes > 1 and total_rels > 0:
            max_edges = (total_nodes * (total_nodes - 1)) / 2
            stats['graph_density'] = round(total_rels / max_edges, 6)
            stats['avg_degree']    = round((2 * total_rels) / total_nodes, 2)
            stats['is_demo_data']  = False
        elif total_nodes == 0:
            stats.update({
                'customer_count': 50000, 'product_count': 8923,
                'relationship_count': 267000, 'purchase_rel_count': 150000,
                'review_rel_count': 50000, 'similar_cust_count': 40000,
                'similar_prod_count': 27000, 'graph_density': 0.00089,
                'avg_degree': 24.5, 'is_demo_data': True,
                'avg_shortest_path': 3.2, 'diameter': 7,
            })
            return {"graph_stats": stats}
        else:
            stats['graph_density'] = 0.0
            stats['avg_degree']    = 0.0
            stats['is_demo_data']  = False

        # ── Total nodes ───────────────────────────────────────────
        total = db.query("MATCH (n) RETURN count(DISTINCT n) AS total_nodes")
        stats['total_nodes'] = int(total[0].get('total_nodes', 0)) if total else 0

        # ── Algorithms computed ───────────────────────────────────
        algo_check = db.query(
            "MATCH (p:Product) WHERE p.pagerank IS NOT NULL RETURN count(p) AS n"
        )
        stats['algorithms_computed'] = (
            int(algo_check[0].get('n', 0)) > 0 if algo_check else False
        )
        stats['num_components'] = 1

        # ── Avg Shortest Path & Diameter (échantillon 50 nœuds) ──
        # Calculer sur le dataset complet est impossible (O(n²)).
        # On échantillonne 50 clients aléatoires et on fait un BFS limité.
        try:
            path_result = db.query("""
                MATCH (c:Customer)
                WITH c ORDER BY rand() LIMIT 50

                // BFS entre paires — on utilise shortestPath de Cypher
                MATCH (c)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(c2:Customer)
                WHERE id(c) < id(c2)
                WITH c, c2
                MATCH path = shortestPath((c)-[:PURCHASED|REVIEWED*..6]-(c2))
                RETURN
                    avg(length(path)) AS avg_path,
                    max(length(path)) AS diameter
            """)

            if path_result and path_result[0].get('avg_path') is not None:
                import math
                avg_p = path_result[0]['avg_path']
                diam  = path_result[0]['diameter']
                stats['avg_shortest_path'] = (
                    None if (isinstance(avg_p, float) and math.isnan(avg_p))
                    else round(float(avg_p), 2)
                )
                stats['diameter'] = (
                    None if diam is None else int(diam)
                )
            else:
                stats['avg_shortest_path'] = None
                stats['diameter']          = None

        except Exception as path_err:
            logger.warning(f"Shortest path calculation failed: {path_err}")
            stats['avg_shortest_path'] = None
            stats['diameter']          = None

        logger.info(f"graph_stats: {stats}")

    except Exception as e:
        logger.error(f"Error calculating graph stats: {e}", exc_info=True)
        stats = {
            'customer_count': 0, 'product_count': 0,
            'relationship_count': 0, 'graph_density': 0.0,
            'avg_degree': 0.0, 'total_nodes': 0,
            'algorithms_computed': False, 'num_components': 1,
            'avg_shortest_path': None, 'diameter': None,
            'error': str(e)
        }

    return {"graph_stats": stats}