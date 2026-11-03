"""V-Dem v16 country-year indicators; large RData file, optional user-supplied local copy."""
import release_runtime
import math
import os
import re
import tempfile
import requests
URL = 'https://raw.githubusercontent.com/vdeminstitute/vdemdata/V16/data/vdem.RData'

def query(country_code, indicator, year_from, year_to, *, local_file=None, limit=100):
    if not re.fullmatch('[A-Z]{3}', country_code) or not re.fullmatch('v2[a-zA-Z0-9_]{1,80}', indicator):
        raise ValueError('use an uppercase three-letter country code and a V-Dem v2 indicator')
    if not 1789 <= year_from <= year_to <= 2025 or not 1 <= limit <= 100:
        raise ValueError('invalid year range or limit')
    import pyreadr

    def parse(path):
        if os.path.getsize(path) > 50000000:
            raise ValueError('source exceeds size limit')
        frame = pyreadr.read_r(path)['vdem']
        if indicator not in frame.columns:
            raise ValueError('indicator not present in v16 country-year data')
        columns = ['country_name', 'country_text_id', 'year', indicator]
        columns += [indicator + x for x in ('_codelow', '_codehigh', '_sd') if indicator + x in frame.columns]
        selected = frame.loc[(frame.country_text_id == country_code) & (frame.year >= year_from) & (frame.year <= year_to), columns]
        total = len(selected)
        records = selected.head(limit).to_dict('records')
        for row in records:
            for key, value in row.items():
                if isinstance(value, float) and (not math.isfinite(value)):
                    row[key] = None
        return {'source': 'Local RData (provenance and version unverified)' if local_file else 'V-Dem Country-Year Dataset v16', 'source_url': local_file if local_file else URL, 'doi': None if local_file else 'https://doi.org/10.23696/vdemds26', 'license': None if local_file else 'CC BY-SA 4.0', 'indicator': indicator, 'total_matches': total, 'records': records}
    if local_file:
        return parse(local_file)
    with tempfile.NamedTemporaryFile(suffix='.RData') as f:
        with requests.get(URL, timeout=120, stream=True) as r:
            r.raise_for_status()
            size = 0
            for chunk in r.iter_content(1024 * 1024):
                size += len(chunk)
                if size > 50000000:
                    raise ValueError('source exceeds size limit')
                f.write(chunk)
        f.flush()
        return parse(f.name)
