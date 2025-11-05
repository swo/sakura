import argparse

import polars as pl


def clean(path: str) -> pl.DataFrame:
    # see https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf
    # {source codes => erroneous or suspect quality codes}
    quality_codes_dict = {
        (313, 314, 315, 322, 335, 343, 344, 346): ["2", "3", "6", "7"],
        (220, 221, 222, 223, 347, 348): ["2", "3"],
    }

    quality_codes = pl.from_dicts(
        [
            {"temperature_Source_Code": source, "temperature_Quality_Code": quality}
            for sources, qualities in quality_codes_dict.items()
            for source in sources
            for quality in qualities
        ]
    )

    return (
        pl.read_csv(
            path,
            columns=[
                "Year",
                "Month",
                "Day",
                "Hour",
                "Minute",
                "temperature",
                "temperature_Source_Code",
                "temperature_Quality_Code",
            ],
            separator="|",
            schema_overrides={"temperature_Quality_Code": pl.String},
        )
        # drop null values
        .filter(pl.col("temperature").is_not_null())
        # remove values with bad error codes
        .join(
            quality_codes,
            on=["temperature_Source_Code", "temperature_Quality_Code"],
            how="anti",
        )
        # parse datetime
        .with_columns(
            pl.col(["Month", "Day", "Hour", "Minute"])
            .cast(pl.String)
            .str.pad_start(2, "0")
        )
        .with_columns(
            datetime=pl.concat_str(
                ["Year", "Month", "Day", "Hour", "Minute"], separator="-"
            ).str.to_datetime("%Y-%m-%d-%H-%M")
        )
        .select(["datetime", "temperature"])
        .sort("datetime")
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    data = clean(args.input)
    data.write_csv(args.output)
