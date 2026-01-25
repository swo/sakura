from typing import Any

import jax.numpy as jnp
import jax.random
import numpy as np
import numpyro
import numpyro.distributions as dist
import numpyro.infer


class Schumacher:
    def __init__(
        self,
        temps: np.ndarray,
        blooms: np.ndarray,
        tC: int = 40,
        muD_lo: float = 100.0,
        muD_hi: float = 200.0,
        sigmaD_scale: float = 10.0,
        sigma_eps: float = 1.0,
        mcmc_params: dict[str, float] = {
            "num_warmup": 250,
            "num_samples": 250,
        },
        seed=42,
    ):
        assert tC == int(tC), "tC must be integer-valued"
        assert temps.ndim == 2
        self.n = temps.shape[0]
        assert temps.shape[1] > tC
        assert blooms.ndim == 1
        assert len(blooms) == self.n

        self.tC = tC
        self.muD_lo = muD_lo
        self.muD_hi = muD_hi
        self.sigmaD_scale = sigmaD_scale
        self.sigma_eps = sigma_eps
        self.mcmc_params = mcmc_params
        self.seed = seed

        self.blooms = blooms

        # clean temperatures: keep only after the end of endodormancy, and make them
        # above-zero
        self.raw_temps = temps
        self.temps = temps.copy()
        temps[:, :tC] = 0.0
        temps[:, tC:] = np.maximum(0.0, temps[:, tC:])

        self.key = jax.random.key(self.seed, impl="threefry2x32")

    @staticmethod
    def _interp(y: np.ndarray, ystar: float, tC: int):
        """
        Take the `y` and get their cumulative sum. Then find the continuous-valued
        quasi-index such that the cumsum at that index would yield `ystar`.
        """
        ytrunc = y[tC:]

        x = jnp.arange(len(ytrunc))
        ycum = jnp.cumsum(ytrunc)
        return jnp.interp(ystar, ycum, x) + tC

    def model(self, blooms: np.ndarray, temps: np.ndarray):
        assert temps.ndim == 2
        n = temps.shape[0]

        if blooms is not None:
            assert blooms.ndim == 1
            assert len(blooms) == n

        muD = numpyro.sample("muD", dist.Uniform(self.muD_lo, self.muD_hi))
        sigmaD = numpyro.sample("sigmaD", dist.HalfCauchy(self.sigmaD_scale))
        zD = numpyro.sample("zD", dist.Uniform(0.0, 1.0), sample_shape=(n,))
        Dstar = numpyro.deterministic("Dstar", muD + sigmaD * zD)
        assert len(Dstar) == n

        # mean of bloom time
        mut = jnp.array(
            [self._interp(temps[i, :], Dstar[i], tC=self.tC) for i in range(n)]
        )
        assert len(mut) == n
        numpyro.sample("obs", dist.Normal(mut, self.sigma_eps), obs=blooms)

    def fit(self):
        self.kernel = numpyro.infer.NUTS(self.model)
        self.mcmc = numpyro.infer.MCMC(self.kernel, **self.mcmc_params)
        self.mcmc.run(self.key, blooms=self.blooms, temps=self.temps)

    def predictive(self):
        return numpyro.infer.Predictive(self.model, self.mcmc.get_samples())
