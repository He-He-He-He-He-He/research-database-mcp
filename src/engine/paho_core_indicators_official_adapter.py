"""PAHO/WHO Core Indicators downloadable CSV, streamed from official ZIP."""
import release_runtime
import csv
import io
import re
import zipfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
PAGE = 'https://opendata.paho.org/en/core-indicators/download-dataset'

def _get(url, max_size):
    with requests.get(url, stream=True, timeout=(15, 60)) as response:
        response.raise_for_status()
        parts = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > max_size:
                raise RuntimeError('PAHO response exceeds safety limit')
            parts.append(chunk)
    return b''.join(parts)

def dataset_url():
    html = _get(PAGE, 3000000)
    s = BeautifulSoup(html, 'html.parser')
    urls = []
    for a in s.find_all('a', href=True):
        u = urljoin(PAGE, a['href'])
        p = urlparse(u)
        if p.scheme == 'https' and p.netloc == 'opendata.paho.org' and re.fullmatch('/sites/default/files/data/\\d{4}-\\d{2}/paho-core-indicators-[0-9-]+\\.zip', p.path):
            urls.append(u)
    if len(set(urls)) != 1:
        raise RuntimeError('PAHO page does not identify a unique core indicators ZIP')
    return urls[0]

def search(country, year='', indicator='', keyword='', offset=0, limit=20):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('Country must be ISO3 uppercase')
    if year and (not isinstance(year, str) or not re.fullmatch('\\d{4}', year)):
        raise ValueError('Year must be four digits')
    if indicator and (not isinstance(indicator, str) or not re.fullmatch('\\d{1,8}', indicator)):
        raise ValueError('Indicator ID must be numeric')
    if not isinstance(keyword, str) or len(keyword) > 120 or (not isinstance(offset, int)) or isinstance(offset, bool) or (offset < 0) or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid filter or pagination')
    url = dataset_url()
    raw = _get(url, 20000000)
    out = []
    count = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files = [i for i in z.infolist() if i.filename.lower().endswith('.csv') and (not i.is_dir())]
        if len(files) != 1 or files[0].file_size > 350000000:
            raise RuntimeError('Unexpected PAHO ZIP content')
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            required = {'country_code_iso3', 'indicator_id', 'label_en', 'period_id', 'VALUE_STRING', 'val', 'source_data_specific', 'preliminary', 'status'}
            if not required.issubset(set(reader.fieldnames or [])):
                raise RuntimeError('Unexpected PAHO CSV schema')
            for row in reader:
                if row['country_code_iso3'] != country or (year and row['period_id'] != year) or (indicator and row['indicator_id'] != indicator) or (keyword and keyword.casefold() not in row['label_en'].casefold()):
                    continue
                if offset <= count < offset + limit:
                    out.append(row)
                count += 1
    return {'source': 'Pan American Health Organization / WHO Core Indicators', 'publication_page': PAGE, 'download_url': url, 'file': files[0].filename, 'filters': {'country': country, 'year': year, 'indicator': indicator, 'keyword': keyword}, 'matched': count, 'offset': offset, 'items': out, 'note': 'Source values and NULL markers retained. Values are often WHO or other organizations estimates rather than independent country counts; consult each row source, status, bounds, measure and notes. Whole ZIP is downloaded and CSV scanned for each request; overlapping regional and country records must not be summed.'}
