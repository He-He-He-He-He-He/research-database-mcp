"""Bangladesh Bank NSDP official SDMX data and catalogue, read only."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.bb.org.bd/econdata/nsdp/'

def _get(url):
    if urlparse(url).hostname != 'www.bb.org.bd' or urlparse(url).scheme != 'https':
        raise ValueError('仅允许官方 HTTPS 域名')
    s = requests.Session()
    s.trust_env = False
    r = s.get(url, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200 or len(r.content) > 8000000:
        raise ValueError('数据响应状态或大小异常')
    return r.content

def catalogue(query=''):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('搜索词无效')
    soup = BeautifulSoup(_get(BASE + 'nsdp_bb.php'), 'html.parser')
    out = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not re.fullmatch('/econdata/nsdp/xml/bgd/[a-zA-Z0-9_]+\\.xml', href):
            continue
        tr = a.find_parent('tr')
        cells = tr.find_all('td') if tr else []
        title = cells[0].get_text(' ', strip=True).split(' Browse Data')[0].split(' Download in SDMX')[0] if cells else ''
        links = [urljoin(BASE, x['href'].strip()) for x in tr.find_all('a', href=True)] if tr else []
        item = {'title': title, 'dataset': href.rsplit('/', 1)[-1][:-4], 'sdmx': urljoin(BASE, href), 'data_and_metadata_links': links}
        if query.casefold() in (title + ' ' + item['dataset']).casefold():
            out.append(item)
    if not out and (not query):
        raise ValueError('官方目录结构发生变化')
    return {'source': BASE + 'nsdp_bb.php', 'count': len(out), 'datasets': out, 'note': '中央银行发布汇总页，具体指标可能由不同官方机构编制；请查各表和元数据。'}

def series(dataset, indicator=None, limit=50, latest=10):
    if not re.fullmatch('[A-Za-z0-9_]{1,60}', dataset):
        raise ValueError('数据集代码无效')
    if indicator is not None and (not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('指标代码无效')
    if not 1 <= limit <= 100 or not 1 <= latest <= 100:
        raise ValueError('limit 和 latest 应为 1–100')
    entries = [x for x in catalogue()['datasets'] if x['dataset'] == dataset]
    if not entries:
        raise ValueError('数据集不在官方目录')
    root = ET.fromstring(_get(entries[0]['sdmx']))
    out = []
    matched = 0
    for elem in root.iter():
        if elem.tag.split('}')[-1] != 'Series':
            continue
        if indicator and elem.attrib.get('INDICATOR') != indicator:
            continue
        matched += 1
        if len(out) >= limit:
            continue
        obs = [x.attrib for x in elem if x.tag.split('}')[-1] == 'Obs']
        out.append({'attributes': elem.attrib, 'observation_count': len(obs), 'observations': obs[-latest:]})
    return {'catalog_entry': entries[0], 'matching_series': matched, 'returned_series': len(out), 'series': out, 'note': '完整 XML 在上游下载；条数与最近观测限制在本地应用。SDMX 原始值、单位倍率与基期未转换，请以表格和元数据核对含义及编制机构。'}

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
