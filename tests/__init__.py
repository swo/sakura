import numpy as np

import sakura


class TestSchumacher:
    def test_interp(self):
        assert sakura.Schumacher._interp(np.array([0, 10, 20, 30]), 25.5) == 2.5
