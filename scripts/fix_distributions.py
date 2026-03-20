"""
scripts/fix_purchases_distribution.py

Corrige la distribution des achats :
- Supprime les achats AUTO-générés des clients qui en ont trop (> 4)
- Redistribue : certains clients passent à 0, 1, 2, 3 ou 4 achats
- Ne touche PAS aux achats originaux (order_id sans préfixe 'AUTO-')

Distribution cible :
    0 achats  → ~25% des clients concernés
    1 achat   → ~20%
    2 achats  → ~20%
    3 achats  → ~20%
    4 achats  → ~15%

Usage :
    python scripts/fix_purchases_distribution.py
"""
from config.database import db
import logging
import random
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Distribution cible : (nombre_achats, probabilité_cumulative)
# rand() < seuil → ce client reçoit ce nombre d'achats
DISTRIBUTION = [
    (0, 0.25),   # 25% → 0 achats  (supprime tout)
    (1, 0.45),   # 20% → 1 achat
    (2, 0.65),   # 20% → 2 achats
    (3, 0.85),   # 20% → 3 achats
    (4, 1.00),   # 15% → 4 achats
]


def random_date() -> str:
    start = date(2023, 1, 1)
    delta = (date(2024, 12, 31) - start).days
    return str(start + timedelta(days=random.randint(0, delta)))


def get_max_order_id() -> int:
    result = db.query(
        """
        MATCH ()-[r:PURCHASED]->()
        WHERE r.order_id =~ '[0-9]+'
        RETURN max(toInteger(r.order_id)) AS max_id
        """
    )
    return int(result[0]["max_id"]) if result and result[0]["max_id"] else 9_000_000


def count_clients_with_exactly_n(n: int) -> int:
    result = db.query(
        """
        MATCH (c:Customer)
        WITH c, COUNT { (c)-[:PURCHASED]->() } AS cnt
        WHERE cnt = $n
        RETURN count(c) AS total
        """,
        {"n": n}
    )
    return int(result[0]["total"]) if result else 0


def show_current_distribution():
    """Affiche la distribution actuelle des achats par client."""
    logger.info("Distribution actuelle :")
    for n in range(6):
        count = count_clients_with_exactly_n(n)
        logger.info(f"  {n} achats : {count:>10,} clients")

    result = db.query(
        """
        MATCH (c:Customer)
        WITH c, COUNT { (c)-[:PURCHASED]->() } AS cnt
        WHERE cnt > 4
        RETURN count(c) AS total
        """
    )
    over4 = int(result[0]["total"]) if result else 0
    logger.info(f"  >4 achats : {over4:>10,} clients")


def fix_batch(batch_size: int, order_id_start: int) -> dict:
    """
    Traite un batch de clients ayant exactement 3 achats AUTO-générés.
    Pour chaque client :
      1. Supprime TOUS ses achats AUTO- (order_id commence par AUTO-)
      2. Lui recrée 0, 1, 2, 3 ou 4 achats selon la distribution cible
    """
    # Seuils cumulatifs pour la distribution
    thresholds = [p for (_, p) in DISTRIBUTION]
    counts     = [n for (n, _) in DISTRIBUTION]

    result = db.query(
        """
        // 1. Cibler les clients avec exactement 3 achats AUTO-générés
        MATCH (c:Customer)-[r:PURCHASED]->()
        WHERE r.order_id STARTS WITH 'AUTO-'
        WITH c, count(r) AS auto_count
        WHERE auto_count = 3
        WITH c LIMIT $batch_size

        // 2. Supprimer leurs achats AUTO-
        MATCH (c)-[r:PURCHASED]->()
        WHERE r.order_id STARTS WITH 'AUTO-'
        DELETE r

        RETURN count(DISTINCT c) AS clients_processed
        """,
        {"batch_size": batch_size}
    )
    clients_processed = int(result[0]["clients_processed"]) if result and result[0] else 0

    if clients_processed == 0:
        return {"clients_processed": 0, "relations_created": 0}

    # 3. Recréer avec la distribution cible
    # On fait ça en Python : pour chaque tranche, créer le bon nombre d'achats
    relations_created = 0

    for target_count, threshold in zip(counts, thresholds):
        if target_count == 0:
            # Ces clients gardent 0 achats — déjà supprimés
            prev = thresholds[counts.index(target_count) - 1] if counts.index(target_count) > 0 else 0.0
            prob = threshold - prev
            continue

        prev_threshold = thresholds[counts.index(target_count) - 1] if counts.index(target_count) > 0 else 0.0
        prob = threshold - prev_threshold

        res = db.query(
            """
            // Clients récemment nettoyés (plus d'achats AUTO-)
            MATCH (c:Customer)
            WHERE NOT (c)-[:PURCHASED { }]->()
               OR NOT EXISTS { (c)-[:PURCHASED]->() }
            WITH c
            WHERE NOT (c)-[:PURCHASED]->()
            WITH c LIMIT $batch_size
            WITH c WHERE rand() < $prob

            // Produits aléatoires
            MATCH (p:Product)
            WITH c, p ORDER BY rand()
            WITH c, collect(p)[0..$n] AS products

            UNWIND products AS p
            CREATE (c)-[:PURCHASED {
                order_id:          'AUTO-' + toString($oid_start + toInteger(rand() * 999999)),
                price_at_purchase: round(p.price * (0.85 + rand() * 0.30), 2),
                quantity:          toInteger(rand() * 4) + 1,
                timestamp:         $dates[toInteger(rand() * size($dates))]
            }]->(p)

            RETURN count(*) AS created
            """,
            {
                "batch_size": clients_processed,
                "prob":       prob,
                "n":          target_count,
                "oid_start":  order_id_start + relations_created,
                "dates":      [random_date() for _ in range(30)],
            }
        )
        created = int(res[0]["created"]) if res and res[0] else 0
        relations_created += created

    return {
        "clients_processed": clients_processed,
        "relations_created": relations_created,
    }


def fix_purchases_distribution(batch_size: int = 5_000):
    """
    Corrige la distribution des achats AUTO-générés.
    Cible les clients avec exactement 3 achats AUTO- et redistribue en 0-4.
    """
    logger.info("=" * 55)
    logger.info("FIX PURCHASES DISTRIBUTION")
    logger.info("=" * 55)

    # Afficher l'état actuel
    show_current_distribution()
    logger.info("─" * 55)

    # Compter les clients à corriger (exactement 3 achats AUTO-)
    result = db.query(
        """
        MATCH (c:Customer)-[r:PURCHASED]->()
        WHERE r.order_id STARTS WITH 'AUTO-'
        WITH c, count(r) AS auto_count
        WHERE auto_count = 3
        RETURN count(c) AS total
        """
    )
    total_to_fix = int(result[0]["total"]) if result and result[0] else 0

    if total_to_fix == 0:
        logger.info("Aucun client avec exactement 3 achats AUTO- — rien à corriger.")
        return

    logger.info(f"Clients à corriger (3 achats AUTO-) : {total_to_fix:,}")
    logger.info(f"Distribution cible :")
    logger.info(f"  0 achats → 25%  (~{int(total_to_fix*0.25):,} clients)")
    logger.info(f"  1 achat  → 20%  (~{int(total_to_fix*0.20):,} clients)")
    logger.info(f"  2 achats → 20%  (~{int(total_to_fix*0.20):,} clients)")
    logger.info(f"  3 achats → 20%  (~{int(total_to_fix*0.20):,} clients)")
    logger.info(f"  4 achats → 15%  (~{int(total_to_fix*0.15):,} clients)")
    logger.info("─" * 55)

    order_id_start    = get_max_order_id() + 1
    iteration         = 0
    total_clients     = 0
    total_relations   = 0

    while True:
        res = fix_batch(
            batch_size=batch_size,
            order_id_start=order_id_start + total_relations,
        )

        if res["clients_processed"] == 0:
            break

        iteration       += 1
        total_clients   += res["clients_processed"]
        total_relations += res["relations_created"]

        # Compter les restants
        remaining_result = db.query(
            """
            MATCH (c:Customer)-[r:PURCHASED]->()
            WHERE r.order_id STARTS WITH 'AUTO-'
            WITH c, count(r) AS auto_count
            WHERE auto_count = 3
            RETURN count(c) AS total
            """
        )
        remaining = int(remaining_result[0]["total"]) if remaining_result else 0

        logger.info(
            f"Batch {iteration:>4} | "
            f"clients : {res['clients_processed']:>6,} | "
            f"relations créées : {res['relations_created']:>7,} | "
            f"restants : {remaining:>8,}"
        )

    # ── Résumé final ──────────────────────────────────────────
    logger.info("─" * 55)
    logger.info(f" Terminé en {iteration} batches")
    logger.info(f"   Clients corrigés    : {total_clients:,}")
    logger.info(f"   Relations recréées  : {total_relations:,}")
    logger.info("")
    logger.info("Distribution finale :")
    show_current_distribution()


