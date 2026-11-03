"""JRC GHSL urban centres 2025 v1.2: infrastructure/health thematic datasets."""
import release_runtime
import csv
import io
import requests
import zipfile
from pypdf import PdfReader
BASE = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_THEME_GLOBE_R2024A/'
DOC = 'https://human-settlement.emergency.copernicus.eu/ghs_ucdb_2024.php'
THEMES = {'infrastructure': 'INFRASTRUCTURES', 'health': 'HEALTH'}

def query(theme, mode='data', country='', keyword='', offset=0, limit=20):
    if theme not in THEMES or mode not in ('data', 'metadata'):
        raise ValueError('invalid theme or mode')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    name = 'GHS_UCDB_THEME_' + THEMES[theme] + '_GLOBE_R2024A'
    url = BASE + name + '/V1-2/' + name + '_V1_2.zip'
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        if mode == 'data':
            with z.open(name + '.csv') as raw:
                rows = list(csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')))
            if rows and (not {'ID_UC_G0', 'GC_UCN_MAI_2025', 'GC_CNT_GAD_2025'}.issubset(rows[0])):
                raise ValueError('unexpected source columns')
            values = [r for r in rows if (not country or r['GC_CNT_GAD_2025'].strip().casefold() == country.strip().casefold()) and (not keyword or keyword.strip().casefold() in r['GC_UCN_MAI_2025'].casefold())]
        else:
            reader = PdfReader(io.BytesIO(z.read(name + '.pdf')))
            values = []
            for i, p in enumerate(reader.pages):
                text = p.extract_text() or ''
                if not keyword or keyword.strip().casefold() in text.casefold():
                    values.append({'pdf_page': i + 1, 'text': text})
    return {'source': url, 'documentation': DOC, 'theme': theme, 'mode': mode, 'version': 'R2024A V1.2', 'archive_bytes': len(response.content), 'total_matches': len(values), 'offset': offset, 'limit': limit, 'rows': values[offset:offset + limit], 'notes': ['Urban centres are modelled spatial entities, not administrative boundaries; 2025 population values are grid-modelled, not census counts.', 'Infrastructure and health variables have different reference years, units and sources; use metadata mode to verify each indicator. Missing symbol “-” is retained, not zero.', 'Road length IN_ROA_LEN_2024 is in metres, road density IN_ROA_DEN_2024 is metres per square metre; data are based on Overture Maps accessed in July 2024, not proof of complete road coverage.', 'Source attributes use third-party data with their own reuse conditions; downloaded ZIP includes official indicator documentation.']}
