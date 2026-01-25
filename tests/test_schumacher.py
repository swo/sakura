import numpy as np

import sakura


def test_interp():
    assert sakura.Schumacher._interp(np.array([0, 10, 10, 10]), 25.5, tC=0) == 2.55
