from scripts.seed_purchases import seed_missing_purchases


if __name__ == "__main__":
    seed_missing_purchases(
        batch_size=900,    
        coverage_pct=0.40,   # 60% des clients sans achats en recevront
                             
    )

    
