"""
routers/algorithms.py
Endpoint pour déclencher manuellement le pipeline GDS complet.
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query
from services.gds import run_all_algorithms, diagnose_customer, list_all_clients, pipeline_graph_info, diagnose_duplicates, customer_stats, list_all_products
from utils.cache import invalidate_all, cache_stats
from utils.pipeline_state import get_pipeline_state

router = APIRouter(prefix="/algorithms", tags=["Algorithmes GDS"])
logger = logging.getLogger(__name__)

_pipeline_state_manager = get_pipeline_state()


@router.post("/run_all")
def trigger_run_all(background_tasks: BackgroundTasks, limit: int = 10000):
    """
    Lance l'intégralité du pipeline GDS en arrière-plan :
    PageRank, Degree, Betweenness, Node Similarity (clients + produits).
    Vide le cache automatiquement à la fin.
    Le pipeline tourne en tâche de fond — la réponse est immédiate.
    """
    if not _pipeline_state_manager.start():
        return {"status": "already_running", "message": "Pipeline déjà en cours."}

    def run():
        try:
            report = run_all_algorithms(limit=limit)
            invalidate_all()
            _pipeline_state_manager.finish(report)
            logger.info("Pipeline GDS terminé avec succès.")
        except Exception as e:
            _pipeline_state_manager.fail(str(e))
            logger.error(f"Pipeline GDS FAILED: {e}", exc_info=True)

    background_tasks.add_task(run)

    return {
        "status": "started",
        "message": f"Pipeline GDS lancé sur {limit} clients. Suivez /algorithms/status.",
    }


@router.get("/status")
def pipeline_status():
    """Retourne l'état du pipeline GDS et les stats de cache."""
    return {
        "pipeline": _pipeline_state_manager.get_status(),
        "cache": cache_stats(),
    }


# ── DIAGNOSTIC ENDPOINTS ──────────────────────────────────────────
@router.get("/diagnose/graphs")
def graph_health():
    """Diagnostic des projections GDS actuellement actives."""
    try:
        return pipeline_graph_info()
    except Exception as e:
        logger.error(f"Error in graph_health: {e}")
        return {"error": str(e), "graphs": {}}


@router.get("/diagnose/client/{client_id}")
def diagnose_client(client_id: str):
    """
    Diagnostic complet pour un client spécifique.
    Vérifie l'existence, les achats, la présence dans les projections, et les scores de similarité.
    """
    try:
        return diagnose_customer(client_id)
    except Exception as e:
        logger.error(f"Error in diagnose_client: {e}")
        return {"client_id": client_id, "error": str(e), "exists": False}


@router.get("/diagnose/clients")
def list_clients(limit: int = Query(default=20, ge=1, le=500)):
    """
    Liste des premiers clients avec leurs statistiques.
    Utile pour vérifier quels clients sont disponibles.
    """
    try:
        clients = list_all_clients(limit=limit)
        return {
            "limit": limit,
            "clients": clients,
        }
    except Exception as e:
        logger.error(f"Error in list_clients: {e}")
        return {
            "limit": limit,
            "clients": [],
            "error": str(e),
        }


@router.get("/diagnose/duplicates")
def check_duplicates():
    """
    Diagnostic des doublons de customers.
    Retourne les customer_ids qui ont plusieurs nodes dans la base.
    """
    try:
        return diagnose_duplicates()
    except Exception as e:
        logger.error(f"Error in check_duplicates: {e}")
        return {"duplicates_found": False, "error": str(e)}


@router.get("/diagnose/stats")
def database_stats():
    """
    Statistiques globales sur les customers et les purchases.
    Utile pour comprendre la couverture des données.
    """
    try:
        return customer_stats()
    except Exception as e:
        logger.error(f"Error in database_stats: {e}")
        return {
            "unique_customer_ids": 0,
            "total_customer_nodes": 0,
            "customers_with_purchases": 0,
            "total_purchases": 0,
            "error": str(e),
        }


@router.get("/diagnose/products")
def list_products(limit: int = Query(default=100, ge=1, le=500)):
    """
    Liste des produits avec leurs statistiques.
    Montre les produits les plus populaires (par nombre d'achats).
    """
    try:
        products = list_all_products(limit=limit)
        return {
            "limit": limit,
            "products": products,
        }
    except Exception as e:
        logger.error(f"Error in list_products: {e}")
        return {
            "limit": limit,
            "products": [],
            "error": str(e),
        }