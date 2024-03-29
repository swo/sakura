# sakura

Forecasts/projections for cherry blossom timing

## Methodology

### Overview

Cherry trees bloom in the spring and then enter dormancy in autumn. The dormant period ends when a certain number of cold days have passed. The tree, sensing that winter is ending, begins growing buds, which grow faster when temperatures are warmer. Thus, lower winter temperatures and higher spring temperatures both contribute to earlier blossom dates.

### DTS model

The Japanese cherry blossom [forecasts](https://sakura.weathermap.jp/en.php) are based on the "DTS" method of [Aono and Moriya (2003)](https://www.jstage.jst.go.jp/article/agrmet/59/2/59_2_165/_pdf/-char/ja).

In this model, endodormancy ends $D_\mathrm{me}$ days after January 1. $D_\mathrm{me}$ is assumed to depend on $\phi$ is the latitude ($\degree$ N), $L$ is the distance from the nearest coast (km), and $T_F$ is the average temperature during January, February, and March ($^\degree$ C). By using observed blossom dates and the DTS calculation below, Aono & Moritz made a single, empirical fit of these parameters to $D_\mathrm{me}$:

$$
D_\mathrm{me} = 136.765 - 7.689 \phi + 0.133 \phi^2 - 1.307 \ln L + 0.144 T_F + 0.285 T_F^2
$$

Aono & Moriya Table 2 shows these values as between day of year 30 and 50, which is somewhere in February.

After dormancy is over, the buds grow at a standard rate per day, when the air temperature is at a standard value. A day at a higher temperature constitutes more than one day transformed to standard temperature (DTS), and a colder day constitues less than one DTS, according to the Arrhenius equation:

$$
\mathrm{DTS}_i = \exp \left\lbrace \frac{E_a(T_i - T_s)}{R T_i T_s} \right\rbrace,
$$

where $i$ is the day, $T_i$ is the air temperature, $T_s$ is the standard temperature (288.2 K), and $E_a = 5.6 \times 10^4 \text{ J mol}^{-1}$ and $R = 8.314 \text{ J mol}^{-1} \text{ K}^{-1}$ are constants.

Buds blossom when a certain, fixed number of DTS have elapsed since $D_\mathrm{me}$.

### Model adapation

#### End of endodormancy $D_\mathrm{me}$

The method of Aono & Moritz is *ad hoc*: the model does not reflect the underlying biological mechanism, and the use of $T_F$ averaged over values that include March is causally inconsistent with predicting $D_\mathrm{me}$ in February.

I use a different approach. Biological data suggests that, to exit endodormancy, cherry trees need to be below a certain threshold temperature, somewhere between 32 and 50 $\degree\text{F}$, for a certain amount of time. This dependency is expressed as "chill units." Trees need to accumulate a certain number of chill units to exit endodormancy. Chill units depend nonlinearly on temperature, with temperatures between 32 $^\degree\text{F}$ and about 40 $^\degree\text{F}$ accumulating substantial chilling, temperatures below freezing accumulating somewhat more chilling, and higher temperatures contributing no chilling, or even reverse chilling.

I assume that trees exit endodormancy after $C^\star$ "chill units." The chill units at day $t$ is the number of days with average temperature below a threshold chill temperature $T_C$:

$$
C(t) = \int_{t=-\infty}^t \mathbb{1}_{T(t') < T_C} \,dt'
$$

I only consider a single location, so $D_\mathrm{me}$ will depend only on winter temperatures and not on other factors like latitude or location.

For the purposes of this model, I interpolate $T(t)$ to allow for continuous $t$, then compute the integral at hourly timepoints.

#### DTS

The Arrhenius equation is approximately linear over the relevant range, so I approximate:

$$
\mathrm{DTS}(t) = A + B T(t) + \mathcal{O}[T(t)^2],
$$

where $A$ and $B$ are constants to be fit. I expect these to be approximately $A = 0.24$ and $B = 0.04$, when using $^\degree$ C.

The full bloom date $t_F$ is the first day such that $\sum_{t=D_\mathrm{me}}^{t_F} \mathrm{DTS}(t)$ reaches some threshold value $\mathrm{DTS}^\star$.

### Model statement

- Data
  - Each season is considered independent of other seasons
  - $T(t)$: temperature on day $t$, in $\degree\text{C}$
  - $B$: day of full flowering (this is the forecast target)
- Model parameters
  - $T_C$: threshold temperature required to produce chill
  - $C^\star$: threshold number of chill units (i.e., days under threshold temperature)
  - $A$: DTS at 0 $\degree\text{C}$.
  - $B$: additional DTS per degree Celcius
  - $\mathrm{DTS}^\star$: threshold number of DTS before full bloom
- Priors and observation processes
  - $T_C \sim \mathrm{Unif}(-2.5, 5.0)$, measured in $\degree$ C
  - $C^\star \sim \mathrm{Unif}(5, 30)$, measured in days below $T_C$
  - $A \sim \mathrm{Norm}(0.24, 0.1)$
  - $B \sim \mathrm{Norm}(0.04, 0.01)$
  - $\mathrm{DTS}^\star \sim \mathrm{Unif}(10, 100)$
  - $\varepsilon \sim \mathrm{Unif}(-7, 7)$, observation error on $t_F$, in days (i.e., $t_F = \hat{t}_F + \varepsilon$)

### Alternative approaches and known limitations

#### End of endodormancy

Aono & Moriya use an empirical approach, concluding that the end of endodormancy (typically in February) depends on the average temperature over January, February, and March. This is not causally consistent (March temperatures cannot affect February biology). Modeling the actual process as understood from biology is not particularly complicated.

#### Sentinel trees

More [sophisticated forecasts](https://www.scmp.com/lifestyle/travel-leisure/article/3215108/why-making-japans-cherry-blossom-forecasts-such-pressurised-job-trouble-those-get-it-wrong) in Japan account for weather data as well as observational data from sentinel trees.

#### Other variables

E.g., [another modeler](https://yuriko-schumacher.github.io/statistical-analysis-of-cherry-blossom-first-bloom-date/) used an empirical approach, concluding that blooms occurs after 400 or 600 cumulative daily degrees during spring.

There are [some](https://rapidminer.com/blog/ksk-analytics-solution/) accounts from machine learning approach concluding that temperature is the main driver of blossom date, not precipitation or sunlight.

## Data sources

### Washington, DC

- EPA
  - [Cherry blossom dates](https://www.epa.gov/climate-indicators/cherry-blossoms) and [data file](https://www.epa.gov/system/files/other-files/2022-09/cherry-blossoms_fig-1.csv)
  - Historical temperatures for DC: <https://www.ncdc.noaa.gov/cdo-web/datasets/GHCND/stations/GHCND:USW00013743/detail>
- NPS
  - <https://www.nps.gov/subjects/cherryblossom/bloom-watch.htm>
  - Stage dates since 2004 (and two earlier peak bloom dates)

### Japan

- Japan Meteorological Agency
  - [Kaggle scrape](https://www.kaggle.com/datasets/ryanglasnapp/japanese-cherry-blossom-data)
  - [Source data](https://www.data.jma.go.jp/sakura/data/index.html)
- Aono et al.
  - [https://www.ncei.noaa.gov/access/paleo-search/study/26430]
  - 1200 years of peak bloom dates and mean March temperatures
  - Kyoto

## Data files

- `scrape_nps.ipynb` produces:
  - `data/nps.csv`: stage dates
  - `data/nps_stages.csv`: order of the stages
- `scrape_aono.ipynb` produces `data/aono.csv`
- `scrape_epa.ipynb` produces `data/epa.csv`
