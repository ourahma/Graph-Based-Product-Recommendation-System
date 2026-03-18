"""
routers/algorithms.py
Endpoint pour déclencher manuellement le pipeline GDS complet.
"""
import logging
import datetime

from fastapi import APIRouter, BackgroundTasks
from services.gds import run_all_algorithms
from utils.cache import invalidate_all, cache_stats

router = APIRouter(prefix="/algorithms", tags=["Algorithmes GDS"])
logger = logging.getLogger(__name__)

_pipeline_status = {"running": False, "last_run": None, "last_report": None, "error": None}


@router.post("/run_all")
def trigger_run_all(background_tasks: BackgroundTasks, limit: int = 10000):
    """
    Lance l'intégralité du pipeline GDS en arrière-plan :
    PageRank, Degree, Betweenness, Node Similarity (clients + produits).
    Vide le cache automatiquement à la fin.
    Le pipeline tourne en tâche de fond — la réponse est immédiate.
    """
    if _pipeline_status["running"]:
        return {"status": "already_running", "message": "Pipeline déjà en cours."}

    def run():
        _pipeline_status["running"] = True
        _pipeline_status["error"] = None
        try:
            report = run_all_algorithms(limit=limit)
            invalidate_all()
            _pipeline_status["last_report"] = report
            _pipeline_status["last_run"] = datetime.datetime.utcnow().isoformat()
            logger.info("Pipeline GDS terminé avec succès.")
        except Exception as e:
            _pipeline_status["error"] = str(e)
            logger.error(f"Pipeline GDS FAILED: {e}", exc_info=True)
        finally:
            _pipeline_status["running"] = False

    
    background_tasks.add_task(run)

    return {
        "status": "started",
        "message": f"Pipeline GDS lancé sur {limit} clients. Suivez /algorithms/status.",
    }


@router.get("/status")
def pipeline_status():
    """Retourne l'état du pipeline GDS et les stats de cache."""
    return {
        "pipeline": _pipeline_status,
        "cache": cache_stats(),
    }