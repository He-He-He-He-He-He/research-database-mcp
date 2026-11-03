"""Springer Nature Experiments 公开网页检索题录；不代表浙大全文权限。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
URL = 'https://experiments.springernature.com/search'
INFO = 'https://libdb.zju.edu.cn/s/lib/libtb/show/991'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 120 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('检索词须为 1–120 字单行文本')
    if type(page) is not int or not 1 <= page <= 500:
        raise ValueError('页码须为 1–500')
    query = keyword.strip()
    try:
        r = requests.get(URL, params={'term': query, 'pageNumber': page}, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError('Springer Experiments 请求失败：' + type(e).__name__) from None
    b = BeautifulSoup(r.text, 'html.parser')
    h = b.find('h1', string=lambda x: bool(x and re.search('\\bresults?\\s+for\\b', x, re.I)))
    if h is None:
        h = next((x for x in b.select('h1') if re.search('\\bresults?\\s+for\\b', x.get_text(' ', strip=True), re.I)), None)
    if not h:
        raise RuntimeError('Springer Experiments 搜索结果页结构异常')
    heading = h.get_text(' ', strip=True)
    match = re.match('^([\\d,]+)\\s+results?\\s+for\\b', heading, re.I)
    if not match or query not in heading:
        raise RuntimeError('Springer Experiments 结果总数或查询回显异常')
    total = int(match.group(1).replace(',', ''))
    nodes = b.select('div.SN_search-Results__searched_content_list')
    pf = b.select_one('#pageNumber')
    if len(nodes) > 10 or (total > 0 and (pf is None or pf.get('value') != str(page))) or (total == 0 and (page != 1 or nodes)) or (total > 0 and (not nodes)):
        raise RuntimeError('Springer Experiments 页码或结果结构异常')
    items = []
    for node in nodes:
        a = node.select_one('a.title')
        href = a.get('href', '') if a else ''
        title = a.get_text(' ', strip=True) if a else ''
        if not title:
            raise RuntimeError('Springer Experiments 题名缺失')
        if re.fullmatch('/articles/10\\.\\d{4,9}/[^\\s?#]+', href):
            doi = href[len('/articles/'):]
            target = urljoin('https://experiments.springernature.com', href)
        else:
            u = urlsplit(href)
            slug = u.path.removeprefix('/articles/')
            track = a.get('data-track-label', '').split(',', 1)[0].strip()
            if u.scheme != 'https' or u.netloc != 'www.nature.com' or u.query or u.fragment or (not re.fullmatch('/articles/[A-Za-z0-9._-]+', u.path)) or (track != '10.1038/' + slug):
                raise RuntimeError('Springer Experiments 题名或 DOI 路径异常')
            doi = track
            target = href

        def txt(css):
            x = node.select_one(css)
            return x.get_text(' ', strip=True) if x else None
        citation = txt('.citation .green-text')
        downloads = txt('.views .green-text')
        items.append({'title': title, 'doi': doi, 'url': target, 'content_type_raw': txt('.content-type'), 'source_raw': txt('.source'), 'year_raw': txt('time.date-time'), 'series_raw': txt('.snippet_source_details > .italics'), 'authors_raw': [x.get_text(' ', strip=True) for x in node.select('.author-name')], 'citations_raw': citation, 'downloads_raw': downloads})
    return {'source': 'Springer Nature Experiments 公开网页题录', 'library_info': INFO, 'query': query, 'page': page, 'upstream_page_size': 10, 'total_raw': total, 'items': items, 'note': '网页公开检索题录，原站每页 10 条；引文和下载数为查询时网页原值，年份、版本及协议类型依源站。此接口不返回摘要、实验步骤或全文；网页可见不证明浙大机构登录或逐篇全文权限。'}
