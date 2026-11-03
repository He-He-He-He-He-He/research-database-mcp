"""WRI/UMD country-year tree-cover-loss data, fixed 2026-04-24 version."""
import release_runtime
import csv, io, re
import requests
BASE = 'https://data-api.globalforestwatch.org/dataset/gadm__tcl__iso_change/v20260424'

def country(iso, start=2001, end=2025):
    if not isinstance(iso, str) or not re.fullmatch('[A-Z]{3}', iso):
        raise ValueError('Use a three-letter uppercase GADM ISO code')
    if any((type(x) is not int for x in (start, end))) or not 2001 <= start <= end <= 2025:
        raise ValueError('Year range must be within 2001–2025')
    sql = "SELECT iso,umd_tree_cover_loss__year,SUM(umd_tree_cover_loss__ha) AS loss_ha,SUM(umd_tree_cover_loss_from_fires__ha) AS fire_ha FROM data WHERE iso = '" + iso + "' AND umd_tree_cover_density_2000__threshold = 30 AND umd_tree_cover_loss__year >= " + str(start) + ' AND umd_tree_cover_loss__year <= ' + str(end) + ' GROUP BY iso,umd_tree_cover_loss__year ORDER BY umd_tree_cover_loss__year'
    with requests.get(BASE + '/download/csv', params={'sql': sql}, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for b in r.iter_content(65536):
            raw.extend(b)
            if len(raw) > 2000000:
                raise ValueError('CSV too large')
        url = r.url
    if raw:
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        if reader.fieldnames != ['iso', 'umd_tree_cover_loss__year', 'loss_ha', 'fire_ha']:
            raise ValueError('Unexpected CSV columns')
        rows = list(reader)
    else:
        rows = []
    return {'source': url, 'dataset': 'gadm__tcl__iso_change', 'dataset_version': 'v20260424', 'metadata': BASE, 'country_code': iso, 'start': start, 'end': end, 'records': rows, 'notes': ['WRI country tabulation of University of Maryland/GLAD Global Forest Change v1.13; 2000 tree-canopy-density threshold 30%, annual loss and loss from fire are in hectares.', 'Tree-cover loss includes harvest, fire and other disturbances and is not identical to permanent deforestation; fire loss is a subset and should not be added to total.', 'Method and sensor changes affect comparisons across years, especially before/after 2015; consult source methods and national boundaries.', 'Fixed 2026 release is not the historical dataset available at an earlier cutoff. Values are unrounded source strings; empty result does not mean zero.']}
