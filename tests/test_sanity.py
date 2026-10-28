import numpy as np
from scipy import stats

from optilab.app import Api


def test_numpy_scipy_available():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert np.mean(data) == 3.0
    assert stats.pearsonr(data, data)[0] == 1.0


def test_api_describe():
    result = Api().describe([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result["mean"] == 3.0
    assert len(result["zscores"]) == 5
