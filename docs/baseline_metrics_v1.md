# Baseline Tabular Detector Performance Report (v1)

This report profiles the metrics achieved by the baseline **XGBoost Classifier** trained on tabular transaction logs, incorporating both real transactions from the PaySim dataset and simulated fraud campaigns executed by the Card Tester Red Team agent.

## Training Configuration
- **Model Type**: Extreme Gradient Boosting (`XGBClassifier`)
- **Hyperparameters**: `n_estimators=50`, `max_depth=4`, `learning_rate=0.1`
- **Feature Set**: Numerical features (`amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`), engineered balance discrepancies (`balance_error_orig`, `balance_error_dest`), destination type flag (`is_merchant`), and one-hot encoded transaction types.
- **Dataset Composition**:
  - Combined sample size: 10096 rows
  - Total Fraud cases: 96 rows (includes real CSV fraud + simulated Card Tester attacks)
  - Train/Test Split: 80% Train, 20% Test (Stratified)

---

## Evaluation Metrics (Held-out Test Split)

| Metric | Score | Status | Target Threshold |
|---|---|---|---|
| **Precision** | 0.9444 | PASS | >= 80% |
| **Recall (True Positive Rate)** | 0.8947 | PASS | >= 85% |
| **F1-Score** | 0.9189 | PASS | >= 80% |
| **ROC-AUC Score** | 0.9930 | PASS | >= 90% |
| **False Positive Rate (FPR)** | 0.0005 | PASS | <= 2.0% |

---

## Confusion Matrix Results
- **True Negatives (TN)**: 2000
- **False Positives (FP)**: 1 (Legitimate flagged as fraud)
- **False Negatives (FN)**: 2 (Fraud missed by detector)
- **True Positives (TP)**: 17 (Correctly caught fraud)

## Key Technical Observations
1. **Balance Error Indicators**: The engineered features `balance_error_orig` and `balance_error_dest` show extremely strong correlation with the positive target class, as normal transactions balance exactly whereas fraud events (synthetic and real) often mismatch in beginning/ending ledger states.
2. **Tabular Path Performance**: Highly performant tabular classification is achieved within milliseconds of inference time, satisfying high-throughput runtime criteria.