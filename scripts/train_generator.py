import os
import pickle
import pandas as pd
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
PAYSIM_PATH = os.path.join(DATA_DIR, "PS_20174392719_1491204439457_log.csv")
IEEE_TRANS_PATH = os.path.join(DATA_DIR, "train_transaction.csv")
SYNTHESIZER_OUT = os.path.join(MODELS_DIR, "synthesizer.pkl")

def train_paysim_generator():
    print("[+] Loading PaySim sample for generator training...")
    # Load 5,000 rows, ensuring we get both fraud and non-fraud transactions
    df = pd.read_csv(PAYSIM_PATH, nrows=200000)
    
    # Stratified sample
    fraud_df = df[df['isFraud'] == 1]
    legit_df = df[df['isFraud'] == 0].sample(n=3000, random_state=42)
    sample_df = pd.concat([fraud_df, legit_df]).sample(frac=1, random_state=42) # shuffle
    
    # Feature selection: only columns that are statistically relevant and simple
    selected_cols = ['type', 'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest', 'isFraud']
    sample_df = sample_df[selected_cols]
    
    # Ensure types are correct
    sample_df['isFraud'] = sample_df['isFraud'].astype(int)
    
    print(f"  - PaySim training sample size: {len(sample_df)} rows ({sample_df['isFraud'].sum()} fraud)")
    
    # Define metadata
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(data=sample_df)
    
    # Setup generator (small epochs for speed)
    print("  - Initializing CTGAN Synthesizer for PaySim...")
    synthesizer = CTGANSynthesizer(metadata, epochs=10, batch_size=500, verbose=True)
    
    print("  - Training PaySim CTGAN model...")
    synthesizer.fit(sample_df)
    print("  - PaySim CTGAN model trained successfully.")
    
    return synthesizer

def train_ieee_generator():
    print("\n[+] Loading IEEE-CIS sample for generator training...")
    df = pd.read_csv(IEEE_TRANS_PATH, nrows=100000)
    
    # Stratified sample
    fraud_df = df[df['isFraud'] == 1]
    legit_df = df[df['isFraud'] == 0].sample(n=3000, random_state=42)
    sample_df = pd.concat([fraud_df, legit_df]).sample(frac=1, random_state=42)
    
    # Clean IEEE-CIS transaction features
    selected_cols = ['TransactionAmt', 'ProductCD', 'card1', 'card2', 'card4', 'card6', 'isFraud']
    sample_df = sample_df[selected_cols]
    
    # Fill missing values to prevent CTGAN fit issues
    sample_df['card2'] = sample_df['card2'].fillna(sample_df['card2'].median())
    sample_df['card4'] = sample_df['card4'].fillna(sample_df['card4'].mode()[0])
    sample_df['card6'] = sample_df['card6'].fillna(sample_df['card6'].mode()[0])
    sample_df['isFraud'] = sample_df['isFraud'].astype(int)
    
    print(f"  - IEEE-CIS training sample size: {len(sample_df)} rows ({sample_df['isFraud'].sum()} fraud)")
    
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(data=sample_df)
    
    print("  - Initializing CTGAN Synthesizer for IEEE-CIS...")
    synthesizer = CTGANSynthesizer(metadata, epochs=10, batch_size=500, verbose=True)
    
    print("  - Training IEEE-CIS CTGAN model...")
    synthesizer.fit(sample_df)
    print("  - IEEE-CIS CTGAN model trained successfully.")
    
    return synthesizer

def main():
    print("[+] Beginning statistical generator training pipeline...")
    
    # Train both synthesizers
    paysim_synth = train_paysim_generator()
    ieee_synth = train_ieee_generator()
    
    # Save the trained generators in a single dictionary artifact
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"\n[+] Serializing synthesizers to {SYNTHESIZER_OUT}...")
    artifacts = {
        'paysim': paysim_synth,
        'ieee': ieee_synth
    }
    
    with open(SYNTHESIZER_OUT, 'wb') as f:
        pickle.dump(artifacts, f)
        
    print("[+] Generator training completed and saved!")

if __name__ == "__main__":
    main()
