from typing import Any

import jax.numpy as jnp
import jax.random
import numpy as np
import numpyro
import numpyro.distributions as dist
import numpyro.infer


class Schumacher:
    default_data_params = {
        "tC": 40,
    }
    default_model_params = {
        "muD_lo": 100.0,
        "muD_hi": 200.0,
        "sigmaD_scale": 10.0,
    }

    default_mcmc_params = {"num_warmup": 1000, "num_samples": 1000}

    def __init__(
        self,
        temps: np.ndarray,
        blooms: np.ndarray,
        data_params: dict[str, Any] | None = None,
        model_params: dict[str, Any] | None = None,
        mcmc_params: dict[str, Any] | None = None,
        seed=42,
    ):
        self.data_params = self.default_data_params | (data_params or {})
        self.model_params = self.default_model_params | (model_params or {})
        self.mcmc_params = self.default_mcmc_params | (mcmc_params or {})

        assert self.data_params["tC"] == int(self.data_params["tC"]), (
            "tC must be integer-valued"
        )

        assert temps.ndim == 2
        self.n = temps.shape[0]
        assert temps.shape[1] > self.data_params["tC"]

        assert blooms.ndim == 1
        assert len(blooms) == self.n
        self.blooms = blooms

        # clean temperatures: keep only after the end of endodormancy, and make them
        # above-zero
        self.raw_temps = temps
        self.temps = np.maximum(0.0, temps[:, self.data_params["tC"] :])

        self.seed = seed

    @staticmethod
    def _interp(y: np.ndarray, ystar: float):
        """
        Take the `y` and get their cumulative sum. Then find the continuous-valued
        quasi-index such that the cumsum at that index would yield `ystar`.
        """
        x = jnp.arange(len(y))
        ycum = jnp.cumsum(y)
        print(f"interp: {x=} {ycum=}")
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
        assert len(Dstar) == n

        mutB = jnp.empty_like(Dstar)

        for i in range(n):
            mutB.at[i].set(cls._interp(temps[i, :], Dstar[i]))

        print(mutB)

        numpyro.sample("obs", dist.Poisson(mutB), obs=blooms)

    def fit(self):
        self.kernel = numpyro.infer.NUTS(self.model)
        self.mcmc = numpyro.infer.MCMC(self.kernel, **self.mcmc_params)

        self.mcmc.run(
            jax.random.key(self.seed),
            blooms=self.blooms,
            temps=self.temps,
            **self.model_params,
        )

    def predict(self):
        return numpyro.infer.Predictive(self.model, self.mcmc.get_samples())
