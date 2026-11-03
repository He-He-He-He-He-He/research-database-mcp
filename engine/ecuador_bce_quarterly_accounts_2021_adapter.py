"""Ecuador BCE detailed quarterly national accounts historical dataset."""
import release_runtime
import csv
import hashlib
import io
import re
import requests
BASE = 'https://www.datosabiertos.gob.ec/dataset/7d5ad4b3-a8f7-42d9-8103-81336a592ea6/resource/'
URL = BASE + '2fe2427a-daeb-4137-a29f-22834f3d5ee0/download/cuentastrimestralesdesagregadas.csv'
DICTIONARY = BASE + 'de2337e9-0620-46cf-8ef7-083ad6cc5694/download/cuentastrimestralesdesagregadas-diccionariodatos.xlsx'
CATALOGUE = 'https://www.datosabiertos.gob.ec/dataset/cuentas-nacionales-trimestrales-desagregadas'
HEAD = ['Tipo Variable', 'Variable', 'Código Industria-Producto', 'Industrias-Productos', 'Unidades', 'Año', 'Trimestre', 'Valor']
NOTES = ['Historical Ecuador central bank dataset covers 2000–2021, not current GDP; official catalogue describes constant-price 2007 base and current-price series.', 'Retain source row unit and type: current and constant prices are different. Per source units many amounts are in thousands of US dollars.', 'Values such as 375,662 are preserved as raw strings: the supplied data dictionary does not explicitly identify the comma as decimal or grouping separator.', 'GDP, industry value added and expenditure components are different measures; values may overlap. Quarterly values are not annual growth rates.', 'The dataset licence in the official catalogue is CC BY; consult the original dictionary and methodology for definitions and reuse.']

def query(start, end, code, mode='all', limit=20, offset=0):
    if type(start) is not int or type(end) is not int or (not 2000 <= start <= end <= 2021) or (not isinstance(code, str)) or (not re.fullmatch('[A-Za-z0-9_-]{1,30}', code)) or (mode not in ('all', 'constant', 'current')) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid range, code, mode or pagination')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 12000000 or b'Tipo Variable;' not in raw[:100]:
        raise ValueError('Unexpected BCE data file')
    reader = csv.DictReader(io.StringIO(raw.decode('latin-1')), delimiter=';')
    if reader.fieldnames != HEAD:
        raise ValueError('Unexpected BCE headings')
    rows = []
    total = 0
    for row in reader:
        if row['Código Industria-Producto'].casefold() != code.casefold():
            continue
        if not row['Año'].isdigit() or not start <= int(row['Año']) <= end:
            continue
        kind = row['Tipo Variable']
        if mode == 'constant' and (not kind.endswith('Valores Constantes')):
            continue
        if mode == 'current' and (not kind.endswith('Valores Corrientes')):
            continue
        if offset <= total < offset + limit:
            rows.append(row)
        total += 1
    return {'source': URL, 'catalogue': CATALOGUE, 'dictionary': DICTIONARY, 'sha256': hashlib.sha256(raw).hexdigest(), 'http_last_modified': r.headers.get('Last-Modified'), 'source_columns': HEAD, 'total_matching': total, 'offset': offset, 'notes': NOTES, 'records': rows}
