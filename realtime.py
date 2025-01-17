# ethical_decision.py

import numpy as np

def ethical_decision(weights, criteria):
    """
    Simple decision-making framework that evaluates ethical decisions based on weights and criteria.
    
    :param weights: List of weights for each criterion (e.g., urgency, equity, resource allocation)
    :param criteria: List of criteria scores (e.g., predicted urgency, fairness, patient need)
    :return: Decision (approved or denied)
    """
    score = np.dot(weights, criteria)
    
    if score > 0.75:
        return "Approved"
    elif score > 0.5:
        return "Conditional Approval"
    else:
        return "Denied"