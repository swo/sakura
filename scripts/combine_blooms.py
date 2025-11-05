import argparse

import polars as pl

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--epa", required=True)
    p.add_argument("--nps", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    # When EPA and NPA both report a bloom date for a year, the NPS date is one day
    # before the EPA date. I therefore move all the EPA dates back by one.
    epa = pl.read_csv(args.epa, try_parse_dates=True).with_columns(
        pl.col("date") - pl.duration(days=1)
    )

    nps = (
        pl.read_csv(args.nps, try_parse_dates=True)
        .filter(pl.col("stage_name") == pl.lit("Peak Bloom"))
        .select(["year", "date"])
    )

    # remove duplicates
    data = pl.concat([epa, nps]).unique().sort("year")

    # check that there is only one date per year (i.e., EPA and NPS report same
    # date for each year)
    assert not data.get_column("year").is_duplicated().any()

    data.write_csv(args.output)
