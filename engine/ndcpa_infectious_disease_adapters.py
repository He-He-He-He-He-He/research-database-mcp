"""国家疾控局全国传染病疫情报告目录及报告原表。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://www.ndcpa.gov.cn'
INDEX = ROOT + '/jbkzzx/c100016/common/list.html'
PATH = re.compile('^/jbkzzx/c100016/(?:common|second)/content/content_\\d+\\.html$')

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.ndcpa.gov.cn':
        raise ValueError('非官方 HTTPS 跳转')
    r.encoding = r.apparent_encoding
    return r.text

def listing(keyword=''):
    html = get(INDEX)
    m = re.search('var\\s+itemObj\\s*=\\s*(\\[.*?\\]);', html, re.S)
    if not m:
        raise ValueError('未找到栏目数据')
    data = json.loads(m.group(1))
    items = []
    for row in data:
        title = row.get('aT', '')
        links = json.loads(row.get('aU', '{}'))
        url = urljoin(ROOT, links.get('common', ''))
        p = urlparse(url)
        if keyword not in title or p.hostname != 'www.ndcpa.gov.cn' or (not PATH.fullmatch(p.path)):
            continue
        items.append({'title': title, 'published_at': row.get('aPd'), 'url': url})
    return {'source_url': INDEX, 'total_embedded': len(data), 'scope': '当前栏目页面内嵌列表，本地标题筛选；不保证含全部历史', 'items': items}

def detail(url, keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.ndcpa.gov.cn' or (not PATH.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受国家疾控局疫情栏目官方 HTTPS 正文')
    s = BeautifulSoup(get(url), 'html.parser')
    body = s.select_one('#detailContent')
    head = s.select_one('h1')
    table = body.select_one('table') if body else None
    if not body or not table:
        raise ValueError('未找到结构化报告原表')
    rows = []
    recognized = False
    for tr in table.find_all('tr'):
        cells = [' '.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            recognized = True
            if not keyword or keyword in cells[0]:
                rows.append(cells)
    if not recognized:
        raise ValueError('未识别表格行，无法确认检索结果')
    return {'source_url': url, 'title': head.get_text(' ', strip=True) if head else '', 'scope': '报告表格原始单元格；数字和上标保留为文本', 'rows': rows, 'report_text_with_notes': body.get_text('\n', strip=True)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('url')
    d.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(listing(a.keyword) if a.command == 'list' else detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
