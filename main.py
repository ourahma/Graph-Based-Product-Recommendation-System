from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv
from routers import recommendations, customers, analytics, algorithms
from scripts.seed_purchases import seed_missing_purchases

load_dotenv()

#  Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

#  Application 
app = FastAPI(
    title="Graph Recommendation API",
    description="""
## Système de recommandation Neo4j GDS

Endpoints disponibles :

### Recommandations
- `GET /recommendations/client/{client_id}` — Top-K produits pour un client (CF + communauté + PageRank)
- `GET /recommendations/product/{product_id}` — Produits similaires (Node Similarity + co-achats)
- `GET /recommendations/top` — Tableau pré-calculé des meilleurs produits
- `GET /recommendations/clients/similar-all` — Tous les pairs des clients similaires
### Clients
- `GET /customers/segments` — Les segments représentent des communautés de clients détectées par l’algorithme de Louvain, où chaque groupe regroupe des utilisateurs ayant des comportements d’achat similaires.
- `GET /customers/segments/{id}` — Clients d'un segment
- `GET /customers/top` — Top clients par montant dépensé

### Analytics
- `GET /analytics/categories` — Insights par catégorie produit
- `GET /analytics/graph-stats` — Statistiques globales du graphe

### Algorithmes GDS
- `POST /algorithms/run_all` — Relancer le pipeline GDS complet
- `GET /algorithms/status` — État du pipeline et du cache
    """,
    version="1.0.0",
)

#  CORS ─
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

#  Routers 
PREFIX = "/api/v1"
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(customers.router,       prefix=PREFIX)
app.include_router(analytics.router,       prefix=PREFIX)
app.include_router(algorithms.router,      prefix=PREFIX)

#  Gestionnaire d'erreurs global ─
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée sur {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur serveur interne.", "error": str(exc)},
    )

#  Health check 
@app.get("/health", tags=["Health"])
def health():
    from config.database import db
    try:
        db.query("RETURN 1 AS ok")
        neo4j_status = "connected"
    except Exception as e:
        neo4j_status = f"error: {e}"
    return {"status": "ok", "neo4j": neo4j_status}


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Graph Recommendation API",
        "docs": "/docs",
        "health": "/health",
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
    )