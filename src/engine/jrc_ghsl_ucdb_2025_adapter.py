"""European Commission JRC 2025 urban-centre general characteristics, v1.2."""
import release_runtime
import csv
import io
import requests
import zipfile
NAME = 'GHS_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A'
URL = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_THEME_GLOBE_R2024A/' + NAME + '/V1-2/' + NAME + '_V1_2.zip'
DOC = 'https://human-settlement.emergency.copernicus.eu/ghs_ucdb_2024.php'

def search(country='', keyword='', offset=0, limit=20):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with z.open(NAME + '.csv') as raw:
            rows = list(csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')))
        readme = z.read('readme_V1_2.txt').decode('utf-8', errors='replace')
    if rows and (not {'GC_UCN_MAI_2025', 'GC_CNT_UNN_2025', 'GC_POP_TOT_2025'}.issubset(rows[0])):
        raise ValueError('unexpected source fields')
    selected = [x for x in rows if (not country or x['GC_CNT_UNN_2025'].strip().casefold() == country.strip().casefold()) and (not keyword or keyword.strip().casefold() in (x['GC_UCN_MAI_2025'] + ' ' + x['GC_UCN_LIS_2025']).casefold())]
    return {'source': URL, 'documentation': DOC, 'version': 'R2024A V1.2', 'archive_bytes': len(r.content), 'archive_readme': readme, 'total_rows': len(rows), 'total_matches': len(selected), 'offset': offset, 'limit': limit, 'rows': selected[offset:offset + limit], 'notes': ['Urban centres are modelled spatial entities, not administrative city boundaries; an urban centre may include several named cities.', 'GC_UCA_KM2_2025 is urban-centre area in square kilometres; GC_POP_TOT_2025 is grid-modelled population, not census counts. Original decimals are preserved.', 'Income classification uses 2022 World Bank country groupings even though the field label contains 2025. A 2025 modelling year does not mean all source inputs are 2025 observations.', 'The JRC archive contains third-party source datasets, including GADM; check individual source reuse conditions before redistribution. Blank values are not zero.']}
