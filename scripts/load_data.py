import os
import sys
import pandas as pd

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PAYSIM_PATH = os.path.join(DATA_DIR, "PS_20174392719_1491204439457_log.csv")
IEEE_TRANS_PATH = os.path.join(DATA_DIR, "train_transaction.csv")
IEEE_IDENT_PATH = os.path.join(DATA_DIR, "train_identity.csv")

def check_files():
    print("[+] Checking dataset files in data/ directory...")
    missing_files = []
    
    for name, path in [
        ("PaySim log", PAYSIM_PATH),
        ("IEEE-CIS transaction", IEEE_TRANS_PATH),
        ("IEEE-CIS identity", IEEE_IDENT_PATH)
    ]:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  - Found {name}: {path} ({size_mb:.2f} MB)")
        else:
            if name != "IEEE-CIS identity":  # identity is optional for baseline
                missing_files.append((name, path))
            else:
                print(f"  - [Optional] {name} not found: {path} (will proceed without identity data)")
                
    if missing_files:
        print("[-] Error: Mandatory files are missing!")
        for name, path in missing_files:
            print(f"    Missing: {name} at {path}")
        print("[-] Please ensure Kaggle datasets are downloaded and placed in the /data directory.")
        sys.exit(1)
    print("[+] All mandatory files are present.")

def profile_paysim():
    print("\n[+] Profiling PaySim Dataset...")
    # Load only a subset of rows to prevent memory overload
    print("  - Reading first 100,000 rows...")
    df = pd.read_csv(PAYSIM_PATH, nrows=100000)
    
    total_rows = 100000 # Just profiled portion
    fraud_count = df['isFraud'].sum()
    legit_count = len(df) - fraud_count
    fraud_ratio = (fraud_count / len(df)) * 100
    
    print(f"  - Sample size: {len(df):,} rows")
    print(f"  - Columns: {list(df.columns)}")
    print(f"  - Fraud class count: {fraud_count:,}")
    print(f"  - Legit class count: {legit_count:,}")
    print(f"  - Fraud ratio: {fraud_ratio:.4f}%")
    
    # Check transaction types
    print("  - Transaction type distribution:")
    type_counts = df['type'].value_counts()
    for t, count in type_counts.items():
        print(f"    {t}: {count:,}")
    
    return df

def profile_ieee():
    print("\n[+] Profiling IEEE-CIS Dataset...")
    print("  - Reading first 50,000 transaction rows...")
    df_trans = pd.read_csv(IEEE_TRANS_PATH, nrows=50000)
    
    fraud_count = df_trans['isFraud'].sum()
    legit_count = len(df_trans) - fraud_count
    fraud_ratio = (fraud_count / len(df_trans)) * 100
    
    print(f"  - Sample size: {len(df_trans):,} rows")
    print(f"  - Columns (first 15): {list(df_trans.columns[:15])}...")
    print(f"  - Fraud class count: {fraud_count:,}")
    print(f"  - Legit class count: {legit_count:,}")
    print(f"  - Fraud ratio: {fraud_ratio:.4f}%")
    
    if os.path.exists(IEEE_IDENT_PATH):
        print("  - Reading first 10,000 identity rows...")
        df_ident = pd.read_csv(IEEE_IDENT_PATH, nrows=10000)
        print(f"  - Identity columns: {list(df_ident.columns[:10])}...")
        df_merged = pd.merge(df_trans, df_ident, on='TransactionID', how='inner')
        print(f"  - Merged sample records count (inner join): {len(df_merged):,}")
        
    return df_trans

def main():
    check_files()
    profile_paysim()
    profile_ieee()
    print("\n[+] Data profiling completed successfully!")

if __name__ == "__main__":
    main()
