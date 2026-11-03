"""Company of Biologists 出版社首页近期题录，不是期刊全文搜索。"""
import release_runtime
import json
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
URL = 'https://www.biologists.com/'
JOURNALS = {'development': 'Development', 'cell_science': 'Journal of Cell Science', 'experimental_biology': 'Journal of Experimental Biology', 'disease_models': 'Disease Models & Mechanisms', 'biology_open': 'Biology Open'}

def parse_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    groups = {}
    for group in soup.select('div.is-style-rss'):
        heading, feed = (group.find('h3'), group.find('ul', class_='wp-block-rss'))
        if heading is None or feed is None:
            continue
        name = heading.get_text(' ', strip=True)
        if name not in JOURNALS.values():
            continue
        if name in groups:
            raise RuntimeError('出版社首页期刊栏目重复，无法可靠解析')
        items = []
        for row in feed.select('li.wp-block-rss__item'):
            link, date = (row.select_one('.wp-block-rss__item-title a'), row.find('time'))
            if not link or not link.get('href') or (not date) or (not date.get('datetime')):
                raise RuntimeError('出版社首页题录结构变化，无法可靠解析')
            href = link['href']
            parsed = urlparse(href)
            if parsed.scheme != 'https' or parsed.hostname != 'journals.biologists.com':
                raise RuntimeError('出版社首页题录链接域名异常')
            items.append({'title': link.get_text(' ', strip=True), 'url': href, 'published': date['datetime'], 'journal': name})
        groups[name] = items
    if set(groups) != set(JOURNALS.values()):
        raise RuntimeError('出版社首页五个期刊栏目不完整，无法可靠解析')
    return groups

def search(keyword='', journal='all', limit=10):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    if journal != 'all' and journal not in JOURNALS:
        raise ValueError('未知期刊')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 25):
        raise ValueError('limit 须为 1 至 25 的整数')
    with requests.get(URL, timeout=25, stream=True) as response:
        response.raise_for_status()
        if urlparse(response.url).hostname != 'www.biologists.com':
            raise RuntimeError('出版社首页重定向至意外域名')
        content = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            content.extend(chunk)
            if len(content) > 4000000:
                raise RuntimeError('出版社首页响应过大')
    content = bytes(content)
    groups = parse_page(content)
    chosen = list(JOURNALS.values()) if journal == 'all' else [JOURNALS[journal]]
    records = [row for name in chosen for row in groups[name]]
    matched = [row for row in records if keyword.casefold() in row['title'].casefold()]
    return {'source': 'The Company of Biologists 出版社官网首页近期文章', 'source_url': URL, 'keyword': keyword, 'journal': journal, 'snapshot_count': len(records), 'snapshot_matching_count': len(matched), 'items': matched[:limit], 'scope': '仅查询官网首页展示的近期题录，关键词为标题本地匹配；不是五刊完整检索，不代表浙大机构认证或全文权限。'}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('keyword', nargs='?', default='')
    parser.add_argument('--journal', choices=['all'] + list(JOURNALS), default='all')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.journal, args.limit), ensure_ascii=False, indent=2))
