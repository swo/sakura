
all: data/nps.csv data/noaa.csv

data/nps.csv: scripts/scrape_nps.py
	python $< --output $@

data/noaa.csv: scripts/scrape_noaa.py
	python $< --output $@
