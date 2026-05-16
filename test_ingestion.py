from src.ingestion.loader import load_all

data = load_all()

for name, df in data.items():
    if isinstance(df, list):
        print(f"{name}: {len(df)} records")
    else:
        print(f"{name}: {len(df)} rows, {len(df.columns)} columns")