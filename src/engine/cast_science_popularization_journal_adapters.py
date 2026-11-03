"""中国科协《科普研究》期刊公开文章检索与正文。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
ROOT = 'https://castjournals.cast.org.cn/joweb/kpyj/CN'

def fetch(url):
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], capture_output=True, check=True).stdout

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入不超过100字符的关键词')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    params = {'keyword': keyword, 'searchResult': '1', 'searchParamsStr': '', 'language': 'CN', 'pageSize': '10', 'pageNum': str(page)}
    obj = json.loads(fetch(ROOT + '/search/keyword?' + urlencode(params)).decode('utf-8-sig'))
    if not isinstance(obj.get('list'), list) or not isinstance(obj.get('total'), int):
        raise ValueError('检索结果结构变化')
    items = []
    for x in obj['list']:
        ext = (x.get('ext') or {}).get('CN') or {}
        issue = x.get('issue') or {}
        identifier = str(x.get('id') or '')
        if not re.fullmatch('\\d+', identifier):
            raise ValueError('文章标识异常')
        items.append({'id': identifier, 'title': ext.get('title'), 'authors': x.get('authorsStrCn'), 'year': issue.get('year'), 'volume': issue.get('volume'), 'issue': issue.get('issue'), 'start_page': x.get('startPage'), 'end_page': x.get('endPage'), 'url': ROOT + '/' + identifier})
    return {'source': ROOT, 'journal': '科普研究', 'keyword': keyword, 'page': page, 'page_size': 10, 'total': obj['total'], 'items': items, 'note': '检索仅限本科普研究期刊，出版日期按期刊卷期字段而非站点上线时间。'}

def detail(identifier):
    if not re.fullmatch('\\d{10,25}', str(identifier)):
        raise ValueError('文章标识无效')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('需要 Beautiful Soup 4') from e
    url = ROOT + '/' + str(identifier)
    s = BeautifulSoup(fetch(url), 'html.parser')
    nodes = s.select('.mag_main_zhengwen_left_div_p')
    if not nodes:
        raise ValueError('未识别正文或无公开正文')
    return {'url': url, 'title': s.find('meta', attrs={'name': 'citation_title'}).get('content') if s.find('meta', attrs={'name': 'citation_title'}) else None, 'paragraphs': [{'paragraph_id': n.get('id'), 'text': n.get_text(' ', strip=True)} for n in nodes], 'note': '仅网页可见文字；图片、表格、公式及引用结构未完整解析。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    d = s.add_parser('detail')
    d.add_argument('id')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page) if a.cmd == 'search' else detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
