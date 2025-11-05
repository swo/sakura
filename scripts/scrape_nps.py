import argparse
import urllib.request

import bs4
import polars as pl


def scrape(url="https://www.nps.gov/subjects/cherryblossom/bloom-watch.htm"):
    # read url
    html = urllib.request.urlopen(url).read()

    # extract the table
    table = bs4.BeautifulSoup(html, features="html.parser").find("table")
    assert table is not None
    records = [
        [cell.text for cell in row.find_all("td")] for row in table.find_all("tr")
    ]

    # keep the stages in left-to-right order
    stages = records[0][1:]

    # change records into a polars table
    data_wide = pl.from_records(records[1:], schema=records[0], orient="row")

    # clean data
    data = (
        # wide to long
        data_wide.unpivot(index="Year", variable_name="stage_name", value_name="date")
        # add stage as an integer index
        .with_columns(
            stage=pl.col("stage_name").replace_strict(
                {stage: i for i, stage in enumerate(stages)}
            )
        )
        .rename({"Year": "year"})
        .with_columns(pl.col("year").cast(pl.Int64))
        # remove * from some dates
        .with_columns(pl.col("date").str.replace("*", "", literal=True))
        # parse dates
        .with_columns(
            pl.format("{} {}", pl.col("date"), pl.col("year")).str.to_date("%b %d %Y")
        )
        .select(["year", "stage", "stage_name", "date"])
    )

    # manually add in the data described in the website text
    data_manual = pl.DataFrame(
        {
            "year": [1990, 1958],
            "stage": stages.index("Peak Bloom"),
            "stage_name": "Peak Bloom",
            "date": ["1990 March 15", "1958 April 18"],
        }
    ).with_columns(
        pl.col("date").str.strptime(pl.Date, "%Y %B %d"), pl.col("stage").cast(pl.Int64)
    )

    return pl.concat([data, data_manual]).sort("date")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()

    data = scrape()
    data.write_csv(args.output)
