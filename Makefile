all: data/bloom_dates.csv data/noaa.csv

data/bloom_dates.csv: scripts/combine_blooms.py data/nps.csv data/epa.csv
	python $< --nps data/nps.csv --epa data/epa.csv --output $@

data/epa.csv: scripts/scrape_epa.py
	python $< --output $@

data/nps.csv: scripts/scrape_nps.py
	python $< --output $@

data/noaa.csv: scripts/get_noaa.py
	python $< --output $@
