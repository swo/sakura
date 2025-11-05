import argparse

import polars as pl


def get_data():
    """
    Data are measured as peak Yoshino blossoms in days since Jan 1 of that year

    See <https://www.epa.gov/climate-indicators/cherry-blossoms>
    """
    url = (
        "https://www.epa.gov/system/files/other-files/2022-09/cherry-blossoms_fig-1.csv"
    )
    raw = pl.read_csv(url, skip_rows=6)

    return (
        raw.with_columns(
            date=pl.format("{}-01-01", pl.col("Year")).str.to_date()
            + pl.duration(days=pl.col("Yoshino peak bloom date"))
        )
        .rename({"Year": "year"})
        .select(["year", "date"])
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()

    data = get_data()
    data.write_csv(args.output)
