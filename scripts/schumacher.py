import polars as pl

import sakura

temps = (
    pl.read_csv("data/noaa.csv", try_parse_dates=True)
    .filter(pl.col("variable") == pl.lit("TMIN"))
    .with_columns(year=pl.col("date").dt.year())
)

complete_years = (
    temps.group_by("year").agg(pl.len()).filter(pl.col("len") >= 365).get_column("year")
).to_list()

temps = (
    temps.filter(pl.col("year").is_in(complete_years))
    .with_columns(t=(pl.col("date") - pl.date(pl.col("year"), 1, 1)).dt.total_days())
    # exclude leap days
    .filter(pl.col("t").is_between(0, 364))
    .select(["year", "t", "temperature"])
    .pivot(on="t", index="year")
    .sort("year")
)

blooms = (
    pl.read_csv("data/bloom_dates.csv", try_parse_dates=True)
    .filter(pl.col("year").is_in(complete_years))
    .with_columns(t=(pl.col("date") - pl.date(pl.col("year"), 1, 1)).dt.total_days())
    .sort("year")
)

assert blooms.height == temps.height
assert (blooms["year"] == temps["year"]).all()

blooms = blooms.get_column("t").to_numpy()
temps = temps.drop("year").to_numpy()

model = sakura.Schumacher(temps=temps, blooms=blooms)
model.fit()
print(model.predict())
