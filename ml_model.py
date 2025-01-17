# ml_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from crisis_management import train_ml_model
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

def prepare_data():
    """
    Loads and prepares the healthcare crisis dataset.
    :return: Processed features and target variables
    """
    data = pd.read_csv('data/healthcare_crisis_data.csv')
    data.fillna(data.mean(), inplace=True)
    data = data.dropna(axis=1, how='any')
    
    X = data.drop('outcome', axis=1)
    y = data['outcome']
    
    return X, y

def evaluate_model(model, X_test, y_test):
    """
    Evaluates the trained ML model on the test data.
    :param model: Trained model
    :param X_test: Test features
    :param y_test: Test target
    :return: Model accuracy and confusion matrix
    """
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    return accuracy, cm