"""USGS MCS 2026 lithium mine production table, verified PDF snapshot."""
import release_runtime
import hashlib
import io
import re
import requests
from pypdf import PdfReader
URL = 'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lithium.pdf'
SHA256 = '53f92ea45c367c36f05919151f7784feda5776095afaf3a25aec795a27be106f'
COUNTRIES = ('United States', 'Argentina', 'Australia', 'Brazil', 'Canada', 'Chile', 'China', 'Mali', 'Portugal', 'Zimbabwe')

def query(country):
    if country not in COUNTRIES:
        raise ValueError('country must match one of the ten source table names exactly')
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        content = r.raw.read(2000001, decode_content=True)
    if len(content) > 2000000 or hashlib.sha256(content).hexdigest() != SHA256:
        raise ValueError('source PDF changed or exceeds limit; require renewed footnote review')
    text = '\n'.join((page.extract_text() or '' for page in PdfReader(io.BytesIO(content)).pages))
    section = text.split('World Mine Production and Reserves:', 1)[1].split('World Resources:', 1)[0]
    match = re.search('^' + re.escape(country) + '\\s+([\\d,]+|W)\\s+([\\d,]+|W)\\s+', section, re.M)
    if not match:
        raise ValueError('source table row unavailable or changed')
    raw = list(match.groups())
    reported = country in ('Argentina', 'Chile')
    if reported:
        if not raw[0].startswith('5'):
            raise ValueError('expected superscript footnote marker absent')
        raw[0] = raw[0][1:]
    records = []
    for i, year in enumerate((2024, 2025)):
        val = raw[i]
        records.append({'year': year, 'value': None if val == 'W' else int(val.replace(',', '')), 'status': 'withheld' if val == 'W' else 'reported' if year == 2024 and reported else 'estimated'})
    return {'source': 'USGS Mineral Commodity Summaries 2026 lithium table', 'source_url': URL, 'source_sha256': SHA256, 'country': country, 'unit': 'metric tons, lithium content', 'records': records}
