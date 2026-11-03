"""Read ONS UK and Great Britain mid-year usual-resident population series."""
import release_runtime
import argparse
import json
from ons_adapters import _get
SERIES = {'UKPOP': 'United Kingdom', 'GBPOP': 'Great Britain'}
BASE = 'https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/timeseries'

def population_series(series='UKPOP', year=None):
    if series not in SERIES:
        raise ValueError('series must be UKPOP or GBPOP')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100)):
        raise ValueError('year must be an integer from 1900 to 2100')
    data = _get(f'{BASE}/{series.lower()}/pop/data')
    desc = data.get('description', {})
    years = data.get('years')
    if desc.get('cdid') != series or desc.get('datasetId') != 'pop' or (not isinstance(years, list)):
        raise ValueError('unexpected ONS population response')
    observations = [x for x in years if year is None or x.get('year') == str(year)]
    return {'source': 'UK Office for National Statistics', 'series': series, 'geography': SERIES[series], 'measure': 'mid-year usually resident population estimate', 'unit': 'persons', 'release_date': desc.get('releaseDate'), 'source_url': f'{BASE}/{series.lower()}/pop', 'observations': observations}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--series', choices=SERIES, default='UKPOP')
    p.add_argument('--year', type=int)
    a = p.parse_args()
    print(json.dumps(population_series(a.series, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
