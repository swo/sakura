import argparse

import polars as pl


def get_data():
    data_raw = pl.read_csv(
        "https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/USW00013743.csv.gz",
        has_header=False,
        new_columns=[
            "id",
            "date",
            "variable",
            "temperature",
            "m_flag",
            "q_flag",
            "s_flag",
            "obs_time",
        ],
    )

    return (
        data_raw.filter(pl.col("variable").is_in(["TMIN", "TMAX", "TAVG"]))
        # fix data columns
        .with_columns(pl.col("date").cast(pl.String).str.to_date("%Y%m%d"))
        .with_columns(pl.col("temperature") / 10)
        # exclude quality-flagged rows (i.e., keep only row with no flag)
        .filter(pl.col("q_flag").is_null())
        .select(["date", "variable", "temperature"])
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()

    data = get_data()
    data.write_csv(args.output)
