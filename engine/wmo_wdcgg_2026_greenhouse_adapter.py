"""WMO WDCGG 27 October 2026 global greenhouse-gas mole fractions."""
import release_runtime
import csv, io
import requests
BASE = 'https://gaw.kishou.go.jp/static/publications/global_mean_mole_fractions/2026/'
NOTES = ['WMO Global Atmosphere Watch / WDCGG global near-surface mole-fraction analysis from selected observation sites, not a single station or satellite column average.', 'CO2 is in ppm; CH4 and N2O are in ppb. Concentration is not emissions. Annual uncertainty is reported at 68% confidence; monthly growth-rate units are per year.', 'This is the 27 October 2026 bulletin vintage. Historical years may have been recalibrated retrospectively, so they are not the figures necessarily available at an earlier cutoff.', 'CSV fields and NaN or missing markers are returned as source strings. Source attribution and applicable WMO/GAW data conditions must be respected.']

def series(gas, frequency='annual', start=1984, end=2100):
    if gas not in ('co2', 'ch4', 'n2o') or frequency not in ('annual', 'monthly') or type(start) is not int or (type(end) is not int) or (not 1800 <= start <= end <= 2100):
        raise ValueError('Invalid gas, frequency or years')
    url = BASE + gas + '_' + frequency + '_20261027.csv'
    with requests.get(url, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 1000000:
                raise ValueError('CSV exceeds size limit')
    reader = csv.DictReader(io.StringIO(bytes(raw).decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or 'year' not in reader.fieldnames:
        raise ValueError('Unexpected CSV header')
    rows = []
    for row in reader:
        if None in row or not str(row.get('year', '')).isdigit():
            raise ValueError('Unexpected CSV row')
        if start <= int(row['year']) <= end:
            rows.append(row)
    return {'source': url, 'vintage_date': '2026-10-27', 'gas': gas, 'frequency': frequency, 'columns': reader.fieldnames, 'notes': NOTES, 'records': rows}
