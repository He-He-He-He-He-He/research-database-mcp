"""Pakistan Bureau of Statistics NSDP: official PBS-hosted SDMX catalogue and series."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.pbs.gov.pk/nsdp/'
HOST = 'www.pbs.gov.pk'

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != HOST:
        raise ValueError('仅允许巴基斯坦统计局 HTTPS 域名')
    s = requests.Session()
    s.trust_env = False
    r = s.get(url, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200 or len(r.content) > 8000000:
        raise ValueError('响应状态或大小异常')
    return r.content

def catalogue(query=''):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('搜索词无效')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    out = []
    for a in soup.find_all('a', href=True):
        url = urljoin(PAGE, a['href'].strip())
        u = urlparse(url)
        if u.scheme != 'https' or u.hostname != HOST or (not re.fullmatch('/wp-content/uploads/2020/07/[A-Za-z0-9_]+\\.xml', u.path, re.I)):
            continue
        tr = a.find_parent('tr')
        td = tr.find_all('td', recursive=False) if tr else []
        if not td:
            continue
        item = {'title': td[0].get_text(' ', strip=True), 'dataset': u.path.rsplit('/', 1)[-1][:-4], 'sdmx': url, 'related_links': [urljoin(PAGE, x['href'].strip()) for x in tr.find_all('a', href=True)]}
        if query.casefold() in (item['title'] + ' ' + item['dataset']).casefold():
            out.append(item)
    if not out and (not query):
        raise ValueError('官方目录结构发生变化')
    return {'source': PAGE, 'count': len(out), 'datasets': out, 'scope': '仅包括统计局域名文件，不包含财政部、央行等外站文件；各系列编制机构查关联资料。'}

def series(dataset, indicator=None, limit=50, latest=10):
    if not re.fullmatch('[A-Za-z0-9_]{1,100}', dataset):
        raise ValueError('数据集代码无效')
    if indicator is not None and (not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('指标代码无效')
    if not 1 <= limit <= 100 or not 1 <= latest <= 100:
        raise ValueError('limit 和 latest 应为 1–100')
    entries = [x for x in catalogue()['datasets'] if x['dataset'] == dataset]
    if len(entries) != 1:
        raise ValueError('数据集不在当前本站目录')
    root = ET.fromstring(_get(entries[0]['sdmx']))
    out = []
    count = 0
    for e in root.iter():
        if e.tag.split('}')[-1] != 'Series' or (indicator and e.attrib.get('INDICATOR') != indicator):
            continue
        count += 1
        if len(out) >= limit:
            continue
        obs = [x.attrib for x in e if x.tag.split('}')[-1] == 'Obs']
        out.append({'attributes': e.attrib, 'observation_count': len(obs), 'observations': obs[-latest:]})
    return {'catalog_entry': entries[0], 'matching_series': count, 'returned_series': len(out), 'series': out, 'note': '完整 XML 下载并按原顺序截取；保留原始值、倍率、频率和基期，须查表格及 IMF 元数据核对单位、时间定义与编制机构。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalogue')
    q.add_argument('query', nargs='?', default='')
    q = s.add_parser('series')
    q.add_argument('dataset')
    q.add_argument('--indicator')
    q.add_argument('--limit', type=int, default=50)
    q.add_argument('--latest', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(catalogue(a.query) if a.cmd == 'catalogue' else series(a.dataset, a.indicator, a.limit, a.latest), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
