import numpy as np
import pandas as pd

from src.base_location import weighted_assignment_cost


def test_weighted_assignment_cost_uses_nearest_base():
    matrix = pd.DataFrame(
        [[0, 5, 10], [5, 0, 3], [10, 3, 0]],
        index=[1, 2, 3],
        columns=[1, 2, 3],
    )
    cost, idx = weighted_assignment_cost(matrix, [1, 2, 3], np.array([1, 1, 1]), [1, 3])
    assert cost == 3
    assert list(idx) == [0, 1, 1]



def test_weighted_assignment_cost_uses_base_to_demand_direction():
    matrix = pd.DataFrame(
        [[0, 1, 100], [50, 0, 100], [1, 100, 0]],
        index=[1, 2, 3],
        columns=[1, 2, 3],
    )
    cost, idx = weighted_assignment_cost(matrix, [1, 2], np.array([1, 1]), [1, 3])
    assert cost == 1
    assert list(idx) == [0, 0]
