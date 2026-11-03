"""央视网《新闻联播》旧网站：按播出日期查节目分条视频索引。"""
import release_runtime
import argparse
import datetime
import json
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def day(date, keyword=''):
    d = datetime.date.fromisoformat(date)
    url = f'https://cctv.cntv.cn/lm/xinwenlianbo/{d:%Y%m%d}.shtml'
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'cctv.cntv.cn' or p.path != urlparse(url).path:
        raise ValueError('页面跳转，日期可能不可用；上游错误页不能视为节目')
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'html.parser')
    nodes = soup.select('ul.title2 li a[href]')
    if not nodes:
        raise ValueError('未找到节目条目，页面结构可能已变化')
    items = []
    for a in nodes:
        title = a.get_text(' ', strip=True)
        if keyword.casefold() in title.casefold():
            items.append({'title': title, 'url': urljoin(url, a['href'])})
    return {'date': date, 'source_url': url, 'total_before_filter': len(nodes), 'keyword_scope': '该日期标题', 'items': items}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('date')
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(day(a.date, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
