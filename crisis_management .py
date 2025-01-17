# crisis_management.py

import pandas as pd
import numpy as np
from scipy.optimize import linprog
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# -------------------------------
# Step 1: Machine Learning Model
# -------------------------------
def train_ml_model(data_path):
    """
    Trains a logistic regression model using healthcare crisis data.
    :param data_path: Path to the dataset (CSV format).
    :return: Trained Logistic Regression model.
    """
    # Load dataset
    data = pd.read_csv(data_path)

    # Split dataset into features (X) and target (y)
    X = data[['urgency', 'severity']]
    y = data['critical']

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Logistic Regression model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

    return model

# -------------------------------
# Step 2: Ethical Decision-Making
# -------------------------------
def ethical_decision(weights, criteria):
    """
    Evaluates the ethical score based on weighted criteria.
    :param weights: List of weights for each criterion.
    :param criteria: List of criteria scores (urgency, severity, etc.).
    :return: Ethical score.
    """
    ethical_score = np.dot(weights, criteria)
    return ethical_score

# -------------------------------
# Step 3: Resource Optimization
# -------------------------------
def optimize_resources(resources, demands):
    """
    Optimizes resource allocation using linear programming.
    :param resources: Dictionary of available resources.
    :param demands: Dictionary of required resources per task.
    :return: Optimized resource allocation.
    """
    # Resource limits
    resource_limits = np.array(list(resources.values()))

    # Coefficients for minimization (inverse of demand importance)
    cost = -np.array(list(demands.values()))

    # Identity matrix for inequality constraints
    A = np.eye(len(resources))

    # Solve the linear programming problem
    result = linprog(c=cost, A_ub=A, b_ub=resource_limits, method="highs")

    if result.success:
        allocation = {key: int(val) for key, val in zip(resources.keys(), result.x)}
        return allocation
    else:
        raise ValueError("Optimization failed.")

# -------------------------------
# Step 4: Main Crisis Management Function
# -------------------------------
def crisis_management_model(data, model, resources):
    """
    Integrates the machine learning model, ethical decision-making, and resource optimization.
    :param data: Crisis data (urgency and severity).
    :param model: Trained ML model.
    :param resources: Available resources for allocation.
    :return: Optimized resource allocation.
    """
    # Predict criticality using the ML model
    urgency = data['urgency']
    severity = data['severity']
    critical = model.predict([[urgency, severity]])[0]

    if critical:
        print("Critical situation detected. Allocating resources...")

        # Ethical decision-making weights and criteria
        weights = [0.7, 0.3]  # Weight for urgency and severity
        criteria = [urgency, severity]

        # Calculate ethical score
        ethical_score = ethical_decision(weights, criteria)
        print(f"Ethical Score: {ethical_score:.2f}")

        # Define resource demands (e.g., per critical case)
        demands = {
            "staff": 1,
            "ICU_beds": 0.8,
            "ventilators": 0.5
        }

        # Optimize resources
        allocation = optimize_resources(resources, demands)
        return allocation
    else:
        return "Non-critical situation. Resources are not allocated."

# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    # Train the ML model
    model = train_ml_model("data/healthcare_crisis_data.csv")

    # Example crisis data
    crisis_data = {
        "urgency": 0.9,
        "severity": 0.7
    }

    # Available resources
    available_resources = {
        "staff": 200,
        "ICU_beds": 150,
        "ventilators": 100
    }

    # Run the crisis management model
    allocation_result = crisis_management_model(crisis_data, model, available_resources)
    print("Resource Allocation Result:")
    print(allocation_result)