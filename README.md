# sakura

Forecasts/projections for cherry blossom timing

## Overview

Cherry trees bloom in the spring and then enter dormancy in autumn. The dormant period ends when a certain number of cold days have passed. The tree, sensing that winter is ending, begins growing buds, which grow faster when temperatures are warmer. Thus, lower winter temperatures and higher spring temperatures both contribute to earlier blossom dates.

## Aono & Moriya (2003)

The Japanese cherry blossom [forecasts](https://sakura.weathermap.jp/en.php) are based on the "DTS" method of [Aono & Moriya (2003)](https://www.jstage.jst.go.jp/article/agrmet/59/2/59_2_165/_pdf/-char/ja).

In this model, endodormancy ends $D_\mathrm{me}$ days after January 1. $D_\mathrm{me}$ is assumed to depend on the latitude $\phi$ ($\degree$ N), the distance $L$, from the nearest coast (km), and the average temperature $T_F$ during January, February, and March ($^\degree$ C). By using observed blossom dates and the DTS calculation below, Aono & Moritz made a single, empirical fit of these parameters to $D_\mathrm{me}$:

$$
D_\mathrm{me} = 136.765 - 7.689 \phi + 0.133 \phi^2 - 1.307 \ln L + 0.144 T_F + 0.285 T_F^2
$$

Aono & Moriya Table 2 shows these values as between day of year 30 and 50, which is somewhere in February. (Note that the use of $T_F$ averaged over values that include March is causally inconsistent with predicting $D_\mathrm{me}$ in February.)

After dormancy is over, the buds grow at a standard rate per day, when the air temperature is at a standard value. Days at higher or lower temperatures are converted to Days Transformed to Standard temperature (DTS) according to the Arrhenius equation:

$$
\mathrm{DTS}_i = \exp \left\lbrace \frac{E_a(T_i - T_s)}{R T_i T_s} \right\rbrace,
$$

where $i$ is the day, $T_i$ is the air temperature, $T_s$ is the standard temperature (288.2 K), and $E_a = 5.6 \times 10^4 \text{ J mol}^{-1}$ and $R = 8.314 \text{ J mol}^{-1} \text{ K}^{-1}$ are constants.

Buds blossom when a certain, fixed number of DTS have elapsed since $D_\mathrm{me}$.

## Current model design

### End of endodormancy

Biological data suggests that endodormancy ends after some number of "chill units." Chill units depend nonlinearly on temperature, with temperatures between 32 $^\degree\text{F}$ and about 40 $^\degree\text{F}$ accumulating substantial chilling, temperatures below freezing accumulating somewhat more chilling, and higher temperatures contributing no chilling, or even reverse chilling.

Let $t_C$ be the continuous-valued time a tree exists endodormancy, $C^\star$ be the number of chill units needed to exit endodormancy, $\theta(t)$ be the air temperature over continuous time $t$, and $f$ be a function that maps temperature to chill units. Then:

$$
C^\star = \int_0^{t_C} f(\theta(t')) \,dt'
$$

where $t=0$ is presumably some time in late summer.

As a first pass, we might approximate $f$ as a simple threshold, such that temperatures below some critical temperature $\theta_C$ accumulate chill units while those above do not:

$$
f(\theta) = \begin{cases}
1 & \theta \leq \theta_C \\
0 & \theta > \theta_C
\end{cases}
$$

### Onset of bloom

Full bloom occurs some number $D^\star$ of DTSs after the tree exits endodormancy. Analogous to the chill units above, we write:

$$
D^\star = \int_{t_C}^{t_C + t_D} g(\theta(t')) \,dt'
$$

where $t_D$ is the number of days from end of endodormancy to full bloom and $g$ maps temperatures to the ratio of DTSs to days.

For $g$, Aono & Moriya use the full Arrhenius equation. However, because the Arrhenius equation is well approximated by a linear function over the relevant range, I assert:

$$
g(\theta) = a + b \theta
$$

where $a$ and $b$ are constants to be fit. I expect these to be approximately $a = 0.24$ and $b = 0.04$ (when using $^\degree$ C).

## Model implementation

Each season is considered independent of other seasons. The forecast target is $t_B$, which in theory is precisely equal to $t_C + t_D$, but here we allow for some small deviation to make the inference equations more manageable.

$$
\begin{aligned}
t_C &= \argmin_t \left| C^\star - \int_0^t f(\theta(t')) \,dt' \right| \\
t_D &= \argmin_t \left| D^\star - \int_{t_C}^{t_C + t_D} g(\theta(t')) \,dt' \right| \\
f(\theta) &= \mathbf{1}_{\theta \leq \theta_C} \\
g(\theta) &= a + b\theta \\
t_B &\sim \mathcal{N}(t_C + t_D, \sigma^2) \\
C^\star &\sim \mathrm{Unif}(5, 30) \\
D^\star &\sim \mathrm{Unif}(10, 100) \\
\theta_C &\sim \mathrm{Unif}(-2.5, 5.0) \\
a &\sim \mathcal{N}(0.24, 0.1) \\
b &\sim \mathcal{N}(0.04, 0.01) \\
\sigma^2 &\sim \mathrm{HalfNorm}(1.0)
\end{aligned}
$$

## Data

[Sub-hourly temperature data](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly) for DC (station `USW00013743` at DCA) is from NOAA.

[NPS has](https://www.nps.gov/subjects/cherryblossom/bloom-watch.htm) bloom dates since 2004 (including two earlier peak bloom dates). [EPA has](https://www.epa.gov/climate-indicators/cherry-blossoms) bloom dates from 1921 to 2022. When both sources report a bloom date for a year, the NPS date is one day before the EPA date. I therefore move all the EPA dates back by one.

### Other data

- Sentinel trees: More [sophisticated forecasts](https://www.scmp.com/lifestyle/travel-leisure/article/3215108/why-making-japans-cherry-blossom-forecasts-such-pressurised-job-trouble-those-get-it-wrong) in Japan account for weather data as well as observational data from sentinel trees.
  - Using [satellite data](https://www.american.edu/cas/faculty/alonzo.cfm)?
- Blooms for other plants, if they come earlier than cherry trees: <https://www.epa.gov/climate-indicators/climate-change-indicators-leaf-and-bloom-dates>
- Japan Meteorological Agency
  - [Kaggle scrape](https://www.kaggle.com/datasets/ryanglasnapp/japanese-cherry-blossom-data)
  - [Source data](https://www.data.jma.go.jp/sakura/data/index.html)
- Aono et al.
  - [https://www.ncei.noaa.gov/access/paleo-search/study/26430]
  - 1200 years of peak bloom dates and mean March temperatures
  - Kyoto

## Prior analyses

[Another modeler](https://yuriko-schumacher.github.io/statistical-analysis-of-cherry-blossom-first-bloom-date/) used an empirical approach, concluding that blooms occurs after 400 or 600 cumulative daily degrees during spring.

There are [some](https://rapidminer.com/blog/ksk-analytics-solution/) accounts from machine learning approach concluding that temperature is the main driver of blossom date, not precipitation or sunlight.
