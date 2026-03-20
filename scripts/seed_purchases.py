"""
scripts/seed_purchases.py
Crée des achats aléatoires pour un sous-ensemble de clients sans purchases.
Distribution : 0, 1, 2, 3 ou 4 achats par client (aléatoire).
Certains clients restent intentionnellement sans achats.

Usage :
    python scripts/seed_purchases.py
"""
from config.database import db
import logging
import random
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def random_date(start_year: int = 2023, end_year: int = 2024) -> str:
    """Génère une date aléatoire au format YYYY-MM-DD."""
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = (end - start).days
    return str(start + timedelta(days=random.randint(0, delta)))


def get_max_order_id() -> int:
    """Récupère le plus grand order_id numérique existant."""
    result = db.query(
        """
        MATCH ()-[r:PURCHASED]->()
        WHERE r.order_id =~ '[0-9]+'
        RETURN max(toInteger(r.order_id)) AS max_id
        """
    )
    return int(result[0]["max_id"]) if result and result[0]["max_id"] else 9_000_000


def count_without_purchases() -> int:
    result = db.query(
        "MATCH (c:Customer) WHERE NOT (c)-[:PURCHASED]->() RETURN count(c) AS n"
    )
    return int(result[0]["n"]) if result else 0


def seed_batch(batch_size: int, coverage_pct: float, order_id_start: int) -> dict:
    """
    Traite un batch de clients sans achats.

    - coverage_pct : % de clients du batch qui recevront des achats (ex: 0.70 = 70%)
    - Les clients sélectionnés reçoivent 1, 2, 3 ou 4 achats (distribution uniforme)
    - Les autres restent sans achats (0)

    Retourne : { "clients_processed": int, "relations_created": int }
    """
    result = db.query(
        """
        // 1. Prendre un batch de clients sans achats
        MATCH (c:Customer)
        WHERE NOT (c)-[:PURCHASED]->()
        WITH c 
        ORDER BY c.client_id
        LIMIT $batch_size
        

        // 2. Garder seulement coverage_pct% d'entre eux (les autres gardent 0 achat)
        WITH c WHERE rand() < $coverage_pct

        // 3. Décider aléatoirement combien d'achats : 1, 2, 3 ou 4
        WITH c, toInteger(rand() * 4) + 1 AS num_purchases

        // 4. Récupérer des produits aléatoires selon la quantité décidée
        MATCH (p:Product)
        WITH c, num_purchases, p ORDER BY rand()
        WITH c, num_purchases, collect(p)[0..num_purchases] AS products

        // 5. Créer les relations avec le bon format
        UNWIND products AS p
        CREATE (c)-[:PURCHASED {
            order_id:          toString($order_id_start + toInteger(rand() * 999999)),
            price_at_purchase: round(p.price * (0.85 + rand() * 0.30), 2),
            quantity:          toInteger(rand() * 4) + 1,
            timestamp:         $dates[toInteger(rand() * size($dates))]
        }]->(p)

        RETURN count(*) AS created
        """,
        {
            "batch_size":     batch_size,
            "coverage_pct":   coverage_pct,
            "order_id_start": order_id_start,
            "dates":          [random_date() for _ in range(50)],
        }
    )
    created = int(result[0]["created"]) if result and result[0] else 0
    return {"relations_created": created}


def seed_missing_purchases(
    batch_size:   int   = 5_000,
    coverage_pct: float = 0.60,   # 60% des clients sans achats en recevront
):
    """
    Crée des achats aléatoires pour un sous-ensemble de clients sans purchases.

    Paramètres
    ----------
    batch_size : int
        Clients traités par batch (défaut 5 000).
    coverage_pct : float
        Fraction des clients sans achats qui en recevront (0.0 à 1.0).
        Ex: 0.60 → 60% recevront 1-4 achats, 40% resteront à 0.
    """
    total_missing = count_without_purchases()
    if total_missing == 0:
        logger.info("✅ Tous les clients ont déjà des achats.")
        return

    clients_to_fill = int(total_missing * coverage_pct)

    logger.info(f"Clients sans achats      : {total_missing:,}")
    logger.info(f"Coverage                 : {coverage_pct*100:.0f}%")
    logger.info(f"Clients qui recevront    : ~{clients_to_fill:,}")
    logger.info(f"Clients qui restent à 0  : ~{total_missing - clients_to_fill:,}")
    logger.info(f"Achats par client        : 1, 2, 3 ou 4 (aléatoire uniforme)")
    logger.info(f"Batch size               : {batch_size:,}")
    logger.info("─" * 55)

    order_id_start = get_max_order_id() + 1
    logger.info(f"order_id départ          : {order_id_start:,}")

    iteration      = 0
    total_created  = 0

    while True:
        res = seed_batch(
            batch_size=batch_size,
            coverage_pct=coverage_pct,
            order_id_start=order_id_start + total_created,
        )

        created   = res["relations_created"]
        iteration += 1
        total_created += created
        remaining = count_without_purchases()

        logger.info(
            f"Batch {iteration:>4} | relations créées : {created:>6,} | "
            f"total : {total_created:>8,} | sans achats restants : {remaining:>8,}"
        )

        # Stopper quand le batch ne produit plus rien
        # (tous les clients "couverts" ont été traités)
        if created == 0:
            break

        # Stopper si le nombre de restants ne diminue plus significativement
        # (les ~40% qui resteront à 0 ne seront jamais traités — c'est voulu)
        expected_remaining = int(total_missing * (1 - coverage_pct))
        if remaining <= expected_remaining * 1.05:
            logger.info(f"Objectif atteint — {remaining:,} clients restent intentionnellement à 0 achats.")
            break

    # ── Résumé final ──────────────────────────────────────────
    logger.info("─" * 55)
    final_missing = count_without_purchases()
    final_filled  = total_missing - final_missing

    logger.info(f"✅ Terminé en {iteration} batches")
    logger.info(f"   Relations créées    : {total_created:,}")
    logger.info(f"   Clients avec achats : {final_filled:,}  (reçu 1-4 achats)")
    logger.info(f"   Clients sans achats : {final_missing:,}  (restent à 0 — voulu)")


