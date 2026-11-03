"""Selected official Jinhua 2022 statistical yearbook HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3552/site/tjnj/nj2022/'
TITLES = {'1-1': '行政区划', '1-5': '全市主要年份国民经济主要指标人均水平', '2-1': '全市历年总户数和总人口数', '2-2': '总户数、总人口及人口变动情况', '2-3': '生育情况', '3-1': '历年农林牧渔业总产值', '15-1': '浙江省国民经济和社会发展总量与速度', '15-5': '地级市市区基本情况'}

def catalog(keyword=''):
    return [{'id': i, 'title': title, 'url': BASE + '2022nj' + i + '.htm'} for i, title in TITLES.items() if keyword in title or keyword in i]

def table(table_id):
    if table_id not in TITLES:
        raise ValueError('selected table ID not found')
    item = next((x for x in catalog() if x['id'] == table_id))
    r = requests.get(item['url'], timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in soup.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables or table_id not in soup.get_text(' ', strip=True):
        raise ValueError('official table missing or changed')
    return {'source': '金华统计年鉴2022', 'id': table_id, 'title': item['title'], 'source_url': item['url'], 'tables': tables, 'text': soup.get_text('\n', strip=True)}
