import argparse
import json
import time

import polars as pl
import pyarrow as pa
import pyarrow.dataset as ds
import requests
import yaml


def get_noaa(
    startdate,
    enddate,
    token: str,
    datasetid="GHCND",
    datatypeid="TMIN",
    stationid="GHCND:USW00013743",
    limit: int = 1000,
):
    """Get NOAA Climate Data Online data"""
    headers = {"token": token}
    r = requests.get(
        "".join(
            [
                "https://www.ncdc.noaa.gov/cdo-web/api/v2/data",
                f"?datasetid={datasetid}",
                f"&datatypeid={datatypeid}",
                f"&stationid={stationid}",
                f"&startdate={startdate}",
                f"&enddate={enddate}",
                "&units=metric",
                f"&limit={limit}",
            ]
        ),
        headers=headers,
    )

    return r


def get_temp_year(year: int, token: str):
    """For one year, get the daily temperature"""
    startdate = f"{year}-01-01"
    enddate = f"{year}-12-31"

    r = get_noaa(startdate, enddate, token)
    r.raise_for_status()
    content = json.loads(r.content)["results"]

    return (
        pl.from_dicts(content)
        .with_columns(pl.col("date").str.to_datetime().cast(pl.Date))
        .with_columns(year=pl.col("date").dt.year())
        .select(["year", "date", "value"])
    )


def read_data(path: str) -> pl.LazyFrame:
    return pl.scan_pyarrow_dataset(
        ds.dataset(path, format="parquet", partitioning="hive")
    )


def write_data(df: pl.DataFrame, path: str):
    ds.write_dataset(
        df.to_arrow(),
        path,
        format="parquet",
        partitioning=ds.partitioning(
            pa.schema([df.to_arrow().schema.field("year")]), flavor="hive"
        ),
        existing_data_behavior="delete_matching",
    )


def scrape_data(path: str, token: str, sleep=0.5):
    data = read_data(path)
    n_rows = data.select(pl.len()).collect().item()

    if n_rows == 0:
        known_years = []
    else:
        known_years = data.select(pl.col("year").unique()).collect().get_column("year")

    needed_years = range(2010, 2024)

    missing_years = set(needed_years) - set(known_years)

    if len(missing_years) > 0:
        print(f"Downloading data for: {missing_years}")

        for year in missing_years:
            print(f"  {year}... ", end="")
            df = get_temp_year(year, token)
            write_data(df, path)
            time.sleep(sleep)
            print("done")

    else:
        print("All data is cached")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--path", default="data/cdo")
    p.add_argument("--secrets", default="secrets.yaml")
    args = p.parse_args()

    with open(args.secrets) as f:
        secrets = yaml.safe_load(f)

    token = secrets["ncdc_key"]
    scrape_data(args.path, token)
