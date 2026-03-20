"""
routers/recommendations.py
Endpoints de recommandation ciblée (client, produit) et top pré-calculé.
"""
from fastapi import APIRouter, HTTPException, Query
from config.database import db
from services.gds import stream_similar_customers
from services.recommendation import (
    recommend_for_client,
    recommend_for_product,
    get_top_products,
)
from utils.pipeline_state import get_pipeline_state

router = APIRouter(prefix="/recommendations", tags=["Recommandations"])
_pipeline_state_manager = get_pipeline_state()


# ── GET /recommendations/client/{client_id} ────────────────────────────────
@router.get("/client/{client_id}")
def reco_for_client(
    client_id: str,
    top_k: int = Query(default=5, ge=1, le=50, description="Nombre de recommandations"),
):
    """
    Retourne les top-K produits recommandés pour un client,
    en combinant Collaborative Filtering, segmentation communautaire et PageRank.
    """
    # Check if pipeline is running
    if _pipeline_state_manager.is_running():
        raise HTTPException(
            status_code=503,
            detail="Le pipeline GDS est actuellement en cours d'exécution. "
                   "Les recommandations seront disponibles une fois le pipeline terminé. "
                   "Vérifiez le statut via /api/v1/algorithms/status.",
        )

    results = recommend_for_client(client_id, top_k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune recommandation pour le client '{client_id}'. "
                   "Vérifiez que les algorithmes GDS ont été exécutés.",
        )
    return {
        "client_id": client_id,
        "top_k": top_k,
        "count": len(results),
        "recommendations": results,
    }


# ── GET /recommendations/product/{product_id} ─────────────────────────────
@router.get("/product/{product_id}")
def reco_for_product(
    product_id: str,
    top_k: int = Query(default=5, ge=1, le=50, description="Nombre de produits similaires"),
):
    """
    Retourne les produits similaires à un produit donné
    via Node Similarity + co-achats. ("Vous aimerez aussi")
    """
    # Check if pipeline is running
    if _pipeline_state_manager.is_running():
        raise HTTPException(
            status_code=503,
            detail="Le pipeline GDS est actuellement en cours d'exécution. "
                   "Les recommandations seront disponibles une fois le pipeline terminé. "
                   "Vérifiez le statut via /api/v1/algorithms/status.",
        )

    results = recommend_for_product(product_id, top_k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun produit similaire trouvé pour '{product_id}'.",
        )
    return {
        "product_id": product_id,
        "top_k": top_k,
        "count": len(results),
        "similar_products": results,
    }


# ── GET /recommendations/top ──────────────────────────────────────────────
@router.get("/top")
def top_recommendations(
    method: str = Query(
        default="pagerank",
        description="Méthode : pagerank | degree | betweenness | combined",
    ),
    limit: int  = Query(default=50, ge=1, le=200),
    category: str | None = Query(default=None, description="Filtre catégorie"),
    brand: str | None    = Query(default=None, description="Filtre marque"),
):
    """
    Tableau pré-calculé des top produits — résultats mis en cache 5 min.
    Idéal pour le dashboard principal.
    """
    # Check if pipeline is running
    if _pipeline_state_manager.is_running():
        raise HTTPException(
            status_code=503,
            detail="Le pipeline GDS est actuellement en cours d'exécution. "
                   "Les recommandations seront disponibles une fois le pipeline terminé. "
                   "Vérifiez le statut via /api/v1/algorithms/status.",
        )

    allowed_methods = {"pagerank", "degree", "betweenness", "combined"}
    if method not in allowed_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Méthode inconnue. Choisissez parmi : {allowed_methods}",
        )
    results = get_top_products(method=method, limit=limit, category=category, brand=brand)
    return {
        "method": method,
        "limit": limit,
        "filters": {"category": category, "brand": brand},
        "count": len(results),
        "products": results,
    }
    
    
@router.get("/clients/similar-all")
def all_similar_clients(
    top_k: int = Query(default=5, ge=1, le=50),
    min_similarity: float = Query(default=0.05, ge=0.0, le=1.0),
):
    """
    Retourne toutes les paires de clients similaires dans le subset GDS.
    """
    if _pipeline_state_manager.is_running():
        raise HTTPException(
            status_code=503,
            detail="Le pipeline GDS est actuellement en cours d'exécution. "
                   "Les recommandations seront disponibles une fois le pipeline terminé. "
                   "Vérifiez le statut via /api/v1/algorithms/status.",
        )

    results = db.query(
        """
        CALL gds.nodeSimilarity.stream('global-customer-product', {
            similarityCutoff: $min_similarity,
            topK: $top_k
        })
        YIELD node1, node2, similarity
        
        // Match clients using internal Neo4j IDs (node1/node2 are integers)
        MATCH (c1:Customer) WHERE id(c1) = node1
        MATCH (c2:Customer) WHERE id(c2) = node2
        
        RETURN
            // ✅ Field names matching frontend expectations
            c1.client_id    AS customer1_id,
            c1.name         AS name_1,
            c1.community    AS community1_id,
            c2.client_id    AS customer2_id,
            c2.name         AS name_2,
            c2.community    AS community2_id,
            round(similarity, 4) AS similarity
        ORDER BY similarity DESC
        """,
        {"min_similarity": min_similarity, "top_k": top_k}
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Aucune similarité trouvée. Vérifiez que le pipeline GDS a été exécuté."
        )

    return {
        "count": len(results),
        "pairs": results,  # ✅ Now contains: customer1_id, customer2_id, community1_id, community2_id, similarity
    }