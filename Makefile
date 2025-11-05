NOAA_URL = https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-station/GHCNh_USW00013743_por.psv


all: data/nps.csv data/noaa.csv

data/nps.csv: scripts/scrape_nps.py
	python $< --output $@

data/noaa.csv: scripts/clean_noaa.py data/raw_noaa.psv
	python $< --input data/raw_noaa.psv --output $@

data/raw_noaa.psv:
	curl --output $@ $(NOAA_URL)
