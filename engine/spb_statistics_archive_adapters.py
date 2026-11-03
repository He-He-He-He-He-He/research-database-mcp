"""国家邮政局统计信息历史分页和正文原表查询。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup
ROOT = 'https://www.spb.gov.cn'
CATALOG = ROOT + '/gjyzj/c100276/common_list.shtml'
ENDPOINT = ROOT + '/common/search/ce2d4d5628314ff7a81553529fb7f6a0'

def fetch(url):
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True, text=True).stdout

def list_page(page=1, keyword=''):
    if not isinstance(page, int) or page < 1:
        raise ValueError('页码必须为正整数')
    query = {'_isAgg': 'true', '_isJson': 'true', '_pageSize': 20, '_template': 'index', '_rangeTimeGte': '', '_channelName': '', 'page': page}
    result = json.loads(fetch(ENDPOINT + '?' + urlencode(query)))
    d = result.get('data', {})
    if not isinstance(d.get('results'), list) or not isinstance(d.get('total'), int):
        raise ValueError('上游分页结构异常')
    rows = [{'title': x.get('title'), 'date': x.get('publishedTimeStr'), 'url': x.get('url')} for x in d['results'] if keyword in (x.get('title') or '')]
    return {'source': CATALOG, 'page': page, 'total': d['total'], 'page_size': 20, 'keyword': keyword, 'items': rows, 'note': '关键词仅筛选指定页标题。'}

def detail(url):
    u = urlsplit(url)
    if u.scheme not in ('http', 'https') or u.hostname != 'www.spb.gov.cn' or u.username or u.password or u.port or (not re.fullmatch('/gjyzj/[A-Za-z0-9/]+/[a-f0-9]{32}\\.shtml', u.path)):
        raise ValueError('仅支持国家邮政局公开栏目文章地址')
    safe = urlunsplit(('https', 'www.spb.gov.cn', u.path, '', ''))
    soup = BeautifulSoup(fetch(safe), 'html.parser')
    body = soup.select_one('.detail-news')
    if body is None:
        raise ValueError('文章结构异常')
    images = [urljoin(safe, x.get('src')) for x in body.find_all('img') if x.get('src')]
    tables = []
    for table in body.find_all('table'):
        tables.append([[{'text': cell.get_text(' ', strip=True), 'rowspan': cell.get('rowspan'), 'colspan': cell.get('colspan')} for cell in tr.find_all(['td', 'th'], recursive=False)] for tr in table.find_all('tr')])
    return {'url': safe, 'title': soup.title.get_text(strip=True) if soup.title else None, 'text': body.get_text('\n', strip=True), 'tables': tables, 'images': images, 'note': '原表保留单元格跨行跨列，未展开；图片未识别。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    l = s.add_parser('list')
    l.add_argument('--page', type=int, default=1)
    l.add_argument('--keyword', default='')
    d = s.add_parser('detail')
    d.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_page(a.page, a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
