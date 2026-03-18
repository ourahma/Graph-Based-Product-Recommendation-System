"""
routers/customers.py
Endpoints segmentation clients (Louvain) et profils.
"""
from fastapi import APIRouter, Query
from services.recommendation import (
    get_segments,
    get_segment_customers,
    get_top_customers,
)

router = APIRouter(prefix="/customers", tags=["Clients"])


@router.get("/segments")
def list_segments(limit: int = Query(default=20, ge=1, le=100)):
    """
    Les segments représentent des communautés de clients détectées par l’algorithme de Louvain, où chaque groupe regroupe des utilisateurs ayant des comportements d’achat similaires.
    """
    results = get_segments(limit=limit)
    return {"count": len(results), "segments": results}


@router.get("/segments/{segment_id}")
def segment_detail(
    segment_id: int,
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Retourne les clients appartenant au segment (communauté) donné.
    """
    results = get_segment_customers(segment_id, limit)
    return {
        "segment_id": segment_id,
        "count": len(results),
        "customers": results,
    }


@router.get("/top")
def top_customers(limit: int = Query(default=20, ge=1, le=100)):
    """
    Top clients par montant total dépensé.
    """
    results = get_top_customers(limit)
    return {"count": len(results), "customers": results}
