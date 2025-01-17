# crisis_management.py

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from ethical_decision import ethical_decision
from resource_optimization import optimize_resources

def train_ml_model(X_train, y_train):
    """
    Train a logistic regression model on the given data.
    :param X_train: Features for training
    :param y_train: Target labels for training
    :return: Trained model
    """
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model

def crisis_management_model(crisis_data, model, resource_constraints):
    """
    A simple crisis management model using ML predictions and ethical decision-making.
    :param crisis_data: Dictionary containing 'urgency' and 'severity'
    :param model: Pre-trained ML model
    :param resource_constraints: Constraints on available resources
    :return: Decision on resource allocation and healthcare actions
    """
    urgency = crisis_data['urgency']
    severity = crisis_data['severity']
    
    # Use ML model to predict the outcome of the crisis
    prediction = model.predict([[urgency, severity]])

    # Apply ethical decision-making
    ethics_weights = [0.5, 0.3, 0.2]
    ethics_criteria = [urgency, severity, 0.5]  # Add fairness, resource distribution metrics
    ethical_decision_result = ethical_decision(ethics_weights, ethics_criteria)

    # Allocate resources based on the ethical decision
    if ethical_decision_result == "Approved":
        return optimize_resources(resource_constraints)
    else:
        return "Crisis response on hold: Ethical concerns raised."