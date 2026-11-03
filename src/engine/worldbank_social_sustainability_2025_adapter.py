"""World Bank 2025 Social Sustainability Global Database local snapshot."""
import release_runtime
import hashlib, math, re
from pathlib import Path
import pandas as pd
from pandas.io.stata import StataMissingValue
SOURCE = 'https://datacatalogfiles.worldbank.org/ddh-published/0061880/DR0087106/ssgd_v2_long.dta'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0061880/social-sustainability-global-database'
DEFAULT = Path(__file__).resolve().parent / 'data' / 'ssgd_v2_long_2025.dta'

def _value(v):
    if isinstance(v, StataMissingValue):
        return str(v)
    if hasattr(v, 'item'):
        v = v.item()
    if isinstance(v, float) and (not math.isfinite(v)):
        return None
    return v

def query(country, keyword='', limit=20, offset=0, path=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (limit, offset))) or not 1 <= limit <= 200 or (not 0 <= offset <= 100000):
        raise ValueError('invalid pagination')
    path = Path(path) if path else DEFAULT
    if not path.is_file():
        raise FileNotFoundError('local 2025 snapshot not found; download official file at source URL')
    if path.stat().st_size > 130000000:
        raise ValueError('snapshot exceeds 130 MB')
    country = country.upper()
    rows = []
    matched = 0
    for df in pd.read_stata(path, chunksize=50000, convert_categoricals=False, convert_missing=True):
        needed = {'countrycode', 'indicator', 'definition', 'category', 'period', 'scale', 'source', 'value', 'adm1_code'}
        if not needed.issubset(df.columns):
            raise ValueError('unexpected STATA columns')
        sub = df[(df['countrycode'] == country) & df['indicator'].str.contains(keyword, case=False, regex=False, na=False)]
        for row in sub.to_dict('records'):
            if offset <= matched < offset + limit:
                rows.append({k: _value(v) for k, v in row.items()})
            matched += 1
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    return {'source': str(path), 'reference_source': SOURCE, 'catalog': CATALOG, 'local_snapshot': str(path), 'sha256': digest, 'country': country, 'matched': matched, 'offset': offset, 'records': rows, 'note': 'Local file provenance and version are unverified; the following describes the expected source only. 2025 database snapshot combining multiple third-party surveys and administrative sources, two waves 2015–2018 and 2019–2022; actual survey period is in each row. Units, population, region and definitions differ; do not treat respondents as entire population or sources as independent evidence. National, gender and subnational groups overlap. adm1_code -99 signifies missing per source labels, retained unchanged. STATA missing codes are retained as dot strings. Verify original data providers and applicable reuse terms.'}
