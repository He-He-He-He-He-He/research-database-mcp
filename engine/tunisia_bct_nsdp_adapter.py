"""Central Bank of Tunisia GOSDMX national summary data catalogue and series."""
import release_runtime
import argparse, json, re, time, xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin, parse_qs
import requests
from bs4 import BeautifulSoup
PAGE = 'https://gosdmx.bct.gov.tn/gosdmx/pnrd?lang=EN'
HOST = 'gosdmx.bct.gov.tn'

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != HOST:
        raise ValueError('仅允许突尼斯央行 HTTPS 域名')
    s = requests.Session()
    s.trust_env = False
    for attempt in range(3):
        try:
            r = s.get(url, timeout=30, allow_redirects=False)
            if r.status_code >= 500 and attempt < 2:
                time.sleep(attempt + 1)
                continue
            r.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
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
        q = parse_qs(u.query)
        if u.scheme != 'https' or u.hostname != HOST or u.path != '/gosdmx/telechargerFichierXML' or (set(q) != {'rubriqueAbbreviation'}) or (len(q['rubriqueAbbreviation']) != 1):
            continue
        code = q['rubriqueAbbreviation'][0]
        if not re.fullmatch('[A-Z0-9]{1,20}', code):
            continue
        tr = a.find_parent('tr')
        td = tr.find_all('td', recursive=False) if tr else []
        if not td:
            continue
        item = {'title': td[0].get_text(' ', strip=True), 'dataset': code, 'sdmx': url, 'related_links': [urljoin(PAGE, x['href'].strip()) for x in tr.find_all('a', href=True)]}
        if query.casefold() in (item['title'] + ' ' + code).casefold():
            out.append(item)
    if not out and (not query):
        raise ValueError('官方目录结构发生变化')
    return {'source': PAGE, 'count': len(out), 'datasets': out, 'note': '央行汇总发布，具体系列可能由其他部门编制，需查关联表格及 IMF 元数据。'}

def series(dataset, indicator=None, limit=50, latest=10):
    if not re.fullmatch('[A-Z0-9]{1,20}', dataset):
        raise ValueError('数据集代码无效')
    if indicator is not None and (not re.fullmatch('[A-Za-z0-9_]{1,120}', indicator)):
        raise ValueError('指标代码无效')
    if not 1 <= limit <= 100 or not 1 <= latest <= 100:
        raise ValueError('limit 和 latest 应为 1–100')
    url = 'https://gosdmx.bct.gov.tn/gosdmx/telechargerFichierXML?rubriqueAbbreviation=' + dataset
    root = ET.fromstring(_get(url))
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
    return {'catalogue': PAGE, 'sdmx': url, 'dataset': dataset, 'matching_series': count, 'returned_series': len(out), 'series': out, 'note': '完整 XML 上游下载、按原顺序截取；保留原始值和倍率，不自动换算。发现 CPI 文件倍率与指数描述不一致，所有单位和口径请对照官方 Excel 及元数据。'}

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
