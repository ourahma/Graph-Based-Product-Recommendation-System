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
    """
    Statistiques globales du graphe Neo4j.
    Returns demo data if database is empty, so UI always shows meaningful values.
    """
    stats = {}

    try:
        # Get customer and product counts
        counts = db.query("""
            MATCH (c:Customer) WITH count(c) AS customers
            MATCH (p:Product)  WITH customers, count(p) AS products
            RETURN customers, products
        """)
        
        if counts and len(counts) > 0:
            stats['customer_count'] = int(counts[0].get('customers', 0))
            stats['product_count'] = int(counts[0].get('products', 0))
            logger.info(f"Graph stats - Customers: {stats['customer_count']}, Products: {stats['product_count']}")
        else:
            stats['customer_count'] = 0
            stats['product_count'] = 0
            logger.warning("No customers or products found in database")

        # Get relationship counts
        rels = db.query("""
            MATCH ()-[r:PURCHASED]->() WITH count(r) AS purchases
            MATCH ()-[r2:REVIEWED]->() WITH purchases, count(r2) AS reviews
            OPTIONAL MATCH ()-[r3:SIMILAR_TO]->()
            OPTIONAL MATCH ()-[r4:PRODUCT_SIMILAR]->()
            RETURN purchases, reviews, count(r3) AS similarity_relations, count(r4) AS product_similarity
        """)
        
        if rels and len(rels) > 0:
            purchases = int(rels[0].get('purchases', 0))
            reviews = int(rels[0].get('reviews', 0))
            similarity = int(rels[0].get('similarity_relations', 0))
            product_sim = int(rels[0].get('product_similarity', 0))
            stats['purchase_rel_count'] = purchases
            stats['review_rel_count'] = reviews
            stats['similar_cust_count'] = similarity
            stats['similar_prod_count'] = product_sim
            stats['relationship_count'] = purchases + reviews + similarity + product_sim
        else:
            stats['relationship_count'] = 0
            stats['purchase_rel_count'] = 0
            stats['review_rel_count'] = 0
            stats['similar_cust_count'] = 0
            stats['similar_prod_count'] = 0

        # Calculate graph density and other metrics
        total_nodes = stats['customer_count'] + stats['product_count']
        total_rels = stats['relationship_count']
        
        logger.info(f"Graph calculation - Total nodes: {total_nodes}, Total rels: {total_rels}")
        
        if total_nodes > 1 and total_rels > 0:
            max_possible_edges = (total_nodes * (total_nodes - 1)) / 2
            stats['graph_density'] = round(total_rels / max_possible_edges, 6) if max_possible_edges > 0 else 0
            stats['avg_degree'] = round((2 * total_rels) / total_nodes, 2) if total_nodes > 0 else 0
        else:
            # If database is empty, show demo data so UI isn't blank
            if total_nodes == 0 and total_rels == 0:
                logger.warning("Database appears to be empty, using demo data")
                stats['customer_count'] = 50000
                stats['product_count'] = 8923
                stats['relationship_count'] = 267000
                stats['purchase_rel_count'] = 150000
                stats['review_rel_count'] = 50000
                stats['similar_cust_count'] = 40000
                stats['similar_prod_count'] = 27000
                stats['graph_density'] = 0.00089
                stats['avg_degree'] = 24.5
                stats['is_demo_data'] = True
            else:
                stats['graph_density'] = 0.0
                stats['avg_degree'] = 0.0
                stats['is_demo_data'] = False

        # Get total nodes
        total = db.query("""
            MATCH (n) RETURN count(DISTINCT n) AS total_nodes
        """)
        stats['total_nodes'] = int(total[0].get('total_nodes', 0)) if total else 0

        # Check if algorithms have been computed
        algo_check = db.query("""
            MATCH (p:Product) WHERE p.pagerank IS NOT NULL
            RETURN count(p) AS products_with_pagerank
        """)
        if algo_check:
            stats['algorithms_computed'] = int(algo_check[0].get('products_with_pagerank', 0)) > 0
        else:
            stats['algorithms_computed'] = False

        stats['num_components'] = 1  # Simplified
        
        logger.info(f"Final graph_density: {stats.get('graph_density', 0)}")
        
    except Exception as e:
        logger.error(f"Error calculating graph stats: {e}", exc_info=True)
        # Return default structure on error
        stats = {
            'customer_count': 0,
            'product_count': 0,
            'relationship_count': 0,
            'graph_density': 0.0,
            'avg_degree': 0.0,
            'total_nodes': 0,
            'algorithms_computed': False,
            'num_components': 1,
            'error': str(e)
        }

    return {"graph_stats": stats}
    