"""Official Zhejiang yearbook numbered tables, editions 2021–2024."""
import release_runtime
import json
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3077/site/flash/tjj/Reports1/'
FOLDERS = {2021: '2021-统计年鉴', 2022: '2022浙江统计年鉴', 2023: '2023浙江统计年鉴', 2024: '2024浙江统计年鉴'}

def _get(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content.decode('utf-8')

def catalog(year, keyword=''):
    if isinstance(year, bool) or year not in FOLDERS:
        raise ValueError('available editions: 2021–2024')
    index = BASE + FOLDERS[year] + '/indexcn.html'
    soup = BeautifulSoup(_get(index), 'html.parser')
    items = []
    for a in soup.select('a[main]'):
        path = a['main']
        if not path.startswith('./cn/html/') or not path.endswith('.html'):
            continue
        title = ' '.join(a.get_text(' ', strip=True).split())
        match = re.match('^(\\d+-\\d+[A-Za-z]?)\\s', title)
        if match and keyword in title:
            items.append({'id': match.group(1), 'title': title, 'url': urljoin(index, path)})
    if not items and (not keyword):
        raise ValueError('yearbook catalog format changed')
    return items

def table(year, table_id):
    matches = [item for item in catalog(year) if item['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table ID not found or ambiguous')
    item = matches[0]
    page = _get(item['url'])
    match = re.search('\\bvar\\s+data\\s*=\\s*', page)
    if not match:
        raise ValueError('embedded table data not found')
    obj, _ = json.JSONDecoder().raw_decode(page[match.end():])
    if not isinstance(obj.get('data'), list):
        raise ValueError('embedded table rows missing')
    return {'source': f'浙江省统计局《浙江统计年鉴-{year}》', 'edition': year, 'source_url': item['url'], 'catalog_url': BASE + FOLDERS[year] + '/indexcn.html', 'id': item['id'], 'title': item['title'], 'rows': obj['data'], 'unit': obj.get('unit'), 'remark': obj.get('remark'), 'merge_cells': obj.get('mergeCells'), 'fixed_rows_top': obj.get('fixedRowsTop')}
