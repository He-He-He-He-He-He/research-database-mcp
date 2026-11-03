"""中国科协科技期刊集群公开跨刊文章检索。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode, urlsplit
ROOT = 'https://castjournals.cast.org.cn/joweb/CN'

def fetch(url):
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], capture_output=True, check=True).stdout

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1—100字符')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    p = {'keyword': keyword, 'searchResult': '1', 'searchParamsStr': '', 'language': 'CN', 'pageSize': '10', 'pageNum': str(page)}
    obj = json.loads(fetch(ROOT + '/search/keyword?' + urlencode(p)).decode('utf-8-sig'))
    if not isinstance(obj.get('list'), list) or not isinstance(obj.get('total'), int):
        raise ValueError('上游返回结构变化')
    out = []
    for x in obj['list']:
        e = (x.get('ext') or {}).get('CN') or {}
        i = x.get('issue') or {}
        out.append({'id': x.get('id'), 'title': e.get('title'), 'journal': e.get('journalTitle'), 'authors': x.get('authorsStrCn'), 'year': i.get('year'), 'volume': i.get('volume'), 'issue': i.get('issue'), 'start_page': x.get('startPage'), 'end_page': x.get('endPage'), 'url': e.get('idUrl')})
    return {'source': ROOT + '/home', 'keyword': keyword, 'page': page, 'page_size': 10, 'total': obj['total'], 'items': out, 'note': '站内跨刊检索，内容与排序以原站为准，非全国学术文献全覆盖。'}

def detail(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'castjournals.cast.org.cn' or (not re.fullmatch('/joweb/[a-zA-Z0-9_-]+/CN/\\d{10,25}', u.path)) or u.query or u.fragment:
        raise ValueError('仅支持本平台文章链接')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('详情需要 Beautiful Soup 4') from e
    s = BeautifulSoup(fetch(url), 'html.parser')
    nodes = s.select('.mag_main_zhengwen_left_div_p')
    if not nodes:
        raise ValueError('未识别公开网页正文')
    return {'url': url, 'paragraphs': [{'paragraph_id': n.get('id'), 'text': n.get_text(' ', strip=True)} for n in nodes], 'note': '仅网页可见正文；图片、图表、公式和参考文献结构未完整提取。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    d = s.add_parser('detail')
    d.add_argument('url')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page) if a.cmd == 'search' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
