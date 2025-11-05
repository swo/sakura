NOAA_URL = https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-station/GHCNh_USW00013743_por.psv


all: data/bloom_dates.csv data/noaa.csv

data/bloom_dates.csv: scripts/combine_blooms.py data/nps.csv data/epa.csv
	python $< --nps data/nps.csv --epa data/epa.csv --output $@

data/epa.csv: scripts/scrape_epa.py
	python $< --output $@

data/nps.csv: scripts/scrape_nps.py
	python $< --output $@

data/noaa.csv: scripts/clean_noaa.py data/raw_noaa.psv
	python $< --input data/raw_noaa.psv --output $@

data/raw_noaa.psv:
	curl --output $@ $(NOAA_URL)
