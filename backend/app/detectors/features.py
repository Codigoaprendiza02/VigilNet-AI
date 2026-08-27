import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# The exact ordered list of features the XGBoost model expects
FEATURE_COLS: List[str] = [
    'amount',
    'oldbalanceOrg',
    'newbalanceOrig',
    'oldbalanceDest',
    'newbalanceDest',
    'balance_error_orig',
    'balance_error_dest',
    'is_merchant',
    'type_CASH_IN',
    'type_CASH_OUT',
    'type_DEBIT',
    'type_PAYMENT',
    'type_TRANSFER'
]

def extract_features(event: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts and engineers features from a raw transaction event.
    Handles nested payload structure (MongoDB) as well as flat structures.
    """
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    def get_val(key: str, default: Any = 0.0):
        # Look in root first, then payload
        if key in event:
            return event[key]
        return payload.get(key, default)

    # Support both amount (PaySim) and TransactionAmt (IEEE-CIS)
    amount = float(get_val("amount", get_val("TransactionAmt", 0.0)))
    oldbalance_org = float(get_val("oldbalanceOrg", 0.0))
    newbalance_orig = float(get_val("newbalanceOrig", 0.0))
    oldbalance_dest = float(get_val("oldbalanceDest", 0.0))
    newbalance_dest = float(get_val("newbalanceDest", 0.0))

    # Feature Engineering
    balance_error_orig = oldbalance_org - newbalance_orig - amount
    balance_error_dest = oldbalance_dest + amount - newbalance_dest

    name_dest = get_val("nameDest", "")
    is_merchant = 1.0 if str(name_dest).startswith('M') else 0.0

    tx_type = str(get_val("type", "PAYMENT")).upper()

    features = {
        'amount': amount,
        'oldbalanceOrg': oldbalance_org,
        'newbalanceOrig': newbalance_orig,
        'oldbalanceDest': oldbalance_dest,
        'newbalanceDest': newbalance_dest,
        'balance_error_orig': balance_error_orig,
        'balance_error_dest': balance_error_dest,
        'is_merchant': is_merchant,
        'type_CASH_IN': 1.0 if tx_type == 'CASH_IN' else 0.0,
        'type_CASH_OUT': 1.0 if tx_type == 'CASH_OUT' else 0.0,
        'type_DEBIT': 1.0 if tx_type == 'DEBIT' else 0.0,
        'type_PAYMENT': 1.0 if tx_type == 'PAYMENT' else 0.0,
        'type_TRANSFER': 1.0 if tx_type == 'TRANSFER' else 0.0,
    }

    return features
