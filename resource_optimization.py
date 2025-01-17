# resource_optimization.py

from scipy.optimize import linprog
import numpy as np

def optimize_resources(resource_constraints):
    """
    Optimizes resource allocation based on available resources and demand.
    :param resource_constraints: List of available resources (e.g., [medical staff, ICU beds, ventilators])
    :return: Optimized allocation of resources
    """
    resources = np.array([200, 150, 100])  # Example: staff, ICU beds, ventilators
    needs = np.array([180, 120, 80])  # Example: patient demand for each resource
    
    # Objective function: maximize resource usage (we minimize the negative)
    c = -np.array([1, 1, 1])  # Negative to maximize the resource usage
    
    # Constraints: resources cannot exceed available supplies
    A = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, -1]])  # Resource constraints
    b = -resources  # Negative of available resources
    
    # Solve the linear programming optimization problem
    result = linprog(c, A_ub=A, b_ub=b)
    
    return result.x  # Optimized resource allocation