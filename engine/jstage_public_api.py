"""Single-page J-STAGE WebAPI article-title search, limited metadata."""
import release_runtime
import requests
from urllib.parse import urlencode
from xml.etree import ElementTree as ET
API = 'https://api.jstage.jst.go.jp/searchapi/do'
ATOM = '{http://www.w3.org/2005/Atom}'
OS = '{http://a9.com/-/spec/opensearch/1.1/}'
PRISM = '{http://prismstandard.org/namespaces/basic/2.0/}'

def parse(xml):
    if len(xml) > 4000000 or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
        raise ValueError('J-STAGE XML 内容不安全或超限')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ValueError('J-STAGE XML 格式异常') from exc
    if root.tag != ATOM + 'feed':
        raise ValueError('J-STAGE feed 格式异常')
    status = root.findtext(ATOM + 'result/' + ATOM + 'status')
    message = root.findtext(ATOM + 'result/' + ATOM + 'message')
    if status not in ('0', 'WARN_002', 'ERR_001'):
        raise ValueError('J-STAGE 返回错误: ' + str(status) + ' ' + str(message))

    def number(tag):
        v = root.findtext(OS + tag)
        return int(v) if v and v.isdigit() else None

    def langmap(e, name):
        n = e.find(ATOM + name)
        return {x.tag.removeprefix(ATOM): ''.join(x.itertext()).strip() for x in n} if n is not None else {}
    items = []
    for entry in [] if status == 'ERR_001' else root.findall(ATOM + 'entry'):
        auth = entry.find(ATOM + 'author')
        authors = {}
        if auth is not None:
            for lang in auth:
                authors[lang.tag.removeprefix(ATOM)] = [''.join(x.itertext()).strip() for x in lang.findall(ATOM + 'name')]

        def value(t):
            x = entry.findtext(t)
            return x.strip() if x else None
        items.append({'title': langmap(entry, 'article_title'), 'article_url': langmap(entry, 'article_link'), 'authors': authors, 'journal': langmap(entry, 'material_title'), 'doi': value(PRISM + 'doi'), 'issn': value(PRISM + 'issn'), 'eissn': value(PRISM + 'eIssn'), 'volume': value(PRISM + 'volume'), 'issue': value(PRISM + 'number'), 'starting_page': value(PRISM + 'startingPage'), 'publication_year': value(ATOM + 'pubyear'), 'updated': value(ATOM + 'updated')})
    return {'status': status, 'message': message, 'total_results': number('totalResults'), 'start_index': number('startIndex'), 'items_per_page': number('itemsPerPage'), 'items': items}

def search(title, start=1, count=5, session=None):
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('标题检索词不能为空且最多 200 字符')
    if type(start) is not int or not 1 <= start <= 1000 or type(count) is not int or (not 1 <= count <= 10):
        raise ValueError('开始序号为 1–1000，单次条数为 1–10')
    params = {'service': 3, 'article': title.strip(), 'start': start, 'count': count}
    response = (session or requests).get(API, params=params, headers={'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=25)
    response.raise_for_status()
    return {'source': 'Powered by J-STAGE (JST)', 'source_home': 'https://www.jstage.jst.go.jp/browse/-char/en', 'source_url': API + '?' + urlencode(params), 'documentation': 'https://www.jstage.jst.go.jp/static/pages/JstageServices/TAB3/-char/en', 'note': '仅标题检索，单次少量元数据；WARN_002 表示命中数超过上游结果上限，需缩小范围。站点禁止大量下载，商业用途须申请许可；著作权与全文权限取决于各出版机构。', 'data': parse(response.content)}
