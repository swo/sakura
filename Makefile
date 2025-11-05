
.PHONY: noaa

data/nps.csv: scripts/scrape_nps.py
	python $< $@

noaa: scripts/scrape_noaa.py
	python $<
