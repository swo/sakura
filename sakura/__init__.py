from typing import Any

import jax.numpy as jnp
import jax.random
import numpy as np
import numpyro
import numpyro.distributions as dist
import numpyro.infer


class Schumacher:
    default_params = {
        "tC": 40,
        "muD_lo": 100.0,
        "muD_hi": 200.0,
        "sigmaD_scale": 10.0,
    }

    def __init__(
        self,
        temps: np.ndarray,
        blooms: np.ndarray,
        params: None | dict[str, Any] = None,
        update_params=True,
        seed=42,
    ):
        if params is None and update_params:
            self.params = self.default_params
        elif params is None and not update_params:
            raise RuntimeError
        elif params is not None and update_params:
            self.params = self.default_params | params
        elif params is not None and not update_params:
            self.params = params
        else:
            raise RuntimeError

        assert self.params["tC"] == int(self.params["tC"]), "tC must be integer-valued"

        assert temps.ndim == 2
        self.n = temps.shape[0]
        assert temps.shape[1] > self.params["tC"]

        assert blooms.ndim == 1
        assert len(blooms) == self.n

        # clean temperatures: keep only after the end of endodormancy, and make them
        # above-zero
        self.raw_temps = temps
        self.temps = np.maximum(0.0, temps[:, self.params["tC"] :])

        self.seed = seed

    @staticmethod
    def _interp(y: np.ndarray, ystar: float):
        """
        Take the `y` and get their cumulative sum. Then find the continuous-valued
        quasi-index such that the cumsum at that index would yield `ystar`.
        """
        x = jnp.arange(len(y))
        ycum = jnp.cumsum(y)
        return jnp.interp(ystar, ycum, x)

    @classmethod
    def model(
        cls,
        blooms: np.ndarray | None,
        temps: np.ndarray,
        muD_lo: float,
        muD_hi: float,
        sigmaD_scale: float,
    ):
        assert temps.ndim == 2
        n = temps.shape[0]

        if blooms is not None:
            assert blooms.ndim == 1
            assert len(blooms) == n

        muD = numpyro.sample("muD", dist.Uniform(muD_lo, muD_hi))
        sigmaD = numpyro.sample("sigmaD", dist.HalfCauchy(sigmaD_scale))
        zD = numpyro.sample("zD", dist.Uniform(0.0, 1.0), sample_shape=(n,))
        Dstar = numpyro.deterministic("Dstar", muD + sigmaD * zD)
        assert isinstance(Dstar, np.ndarray)
        assert len(Dstar) == n

        mutB = np.array(cls._interp(temps[i, :], Dstar[i]) for i in jnp.arange(n))
        numpyro.sample("obs", dist.Poisson(mutB), obs=blooms)

    def fit(self, mcmc_options: dict = {}):
        self.kernel = numpyro.infer.NUTS(self.model)
        self.mcmc = numpyro.infer.MCMC(self.kernel, **mcmc_options)

        self.mcmc.run(jax.random.key(self.seed), **self.params)

    def predict(self):
        return numpyro.infer.Predictive(self.model, self.mcmc.get_samples())
