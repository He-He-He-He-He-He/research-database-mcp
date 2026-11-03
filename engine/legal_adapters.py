"""法院公开指导性案例及国家法律法规数据库，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
from research import fetch, get
COURT = 'https://www.court.gov.cn'
LAW = 'https://flk.npc.gov.cn/law-search'

class CaseList(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_list = False
        self.depth = 0
        self.items = []
        self.in_date = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'div' and 'sec_list' in a.get('class', '').split():
            self.in_list = True
            self.depth = 1
            return
        if self.in_list and tag == 'div':
            self.depth += 1
        if self.in_list and tag == 'a' and re.fullmatch('/fabu/xiangqing/\\d+\\.html', a.get('href', '')):
            self.items.append({'title': a.get('title', ''), 'url': urljoin(COURT, a['href']), 'date': None})
        if self.in_list and tag == 'i' and ('date' in a.get('class', '').split()):
            self.in_date = True

    def handle_data(self, data):
        if self.in_date and self.items and data.strip():
            self.items[-1]['date'] = data.strip()

    def handle_endtag(self, tag):
        if tag == 'i':
            self.in_date = False
        if self.in_list and tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.in_list = False

class CaseDetail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.text = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.depth and tag == 'div' and ('txt_txt' in attrs.get('class', '').split()):
            self.depth = 1
            self.found = True
            return
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag in ('br', 'p'):
                self.text.append('\n')

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1
        if self.depth and tag == 'p':
            self.text.append('\n')

def guidance_list(page=1, keyword=''):
    if type(page) is not int or not 1 <= page <= 100 or (not isinstance(keyword, str)):
        raise ValueError('page 必须为 1 至 100 的整数，关键词须为字符串')
    url = COURT + '/fabu/gengduo/151' + ('' if page == 1 else '_' + str(page)) + '.html'
    parser = CaseList()
    parser.feed(fetch(url))
    if not parser.items:
        raise ValueError('未找到案例，可能超出页数或网页结构变化')
    return {'source': url, 'page': page, 'scope': '只在当前列表页按标题筛选；效力及是否继续参照需核对后续公告', 'items': [i for i in parser.items if keyword.casefold() in i['title'].casefold()]}

def guidance_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str) or any((type(x) is not int for x in (start_page, end_page))) or (not 1 <= start_page <= end_page <= 100) or (end_page - start_page >= 20):
        raise ValueError('关键词或页码无效，每次最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        r = guidance_list(page)
        sources.append(r['source'])
        for item in r['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新；请重新查询')
            seen.add(item['url'])
            if keyword.casefold() in item['title'].casefold():
                items.append(item)
    return {'source': '最高人民法院指导性案例栏目', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定页标题，目录动态变化，跨页非原子快照，不代表全部案例。指导性案例是否继续参照须核对后续公告。'}

def guidance_detail(id):
    if not re.fullmatch('\\d{1,12}', str(id)):
        raise ValueError('案例页面 ID 必须为数字')
    url = COURT + '/fabu/xiangqing/' + str(id) + '.html'
    parser = CaseDetail()
    parser.feed(fetch(url))
    if not parser.found:
        raise ValueError('未找到正文；网页可能改版')
    return {'source': url, 'text': ''.join(parser.text).strip(), 'note': '指导性案例并非裁判文书网全文；是否继续参照请核对后续公告。'}

def law_search(keyword, page=1, size=10, status=None, search_range=1, category=None, agency=None, year=None):
    if not isinstance(keyword, str) or not keyword.strip() or type(page) is not int or (type(size) is not int) or (type(search_range) is not int) or (status is not None and type(status) is not int) or (not 1 <= page <= 10000) or (not 1 <= size <= 50) or (search_range not in (1, 2)) or (status not in (None, 1, 2, 3, 4)):
        raise ValueError('请检查关键词、页码、每页数量、检索范围或效力状态')
    for name, value in [('category', category), ('agency', agency), ('year', year)]:
        if value is not None and (type(value) is not int or value < 0 or value > 9999):
            raise ValueError(name + ' 必须为 0 至 9999 的整数')
    if year is not None and year < 1900:
        raise ValueError('year 必须为 1900 至 9999')
    result = get(LAW + '/search/list', body={'searchRange': search_range, 'sxrq': [], 'gbrq': [], 'searchType': 2, 'sxx': [] if status is None else [status], 'gbrqYear': [] if year is None else [year], 'flfgCodeId': [] if category is None else [category], 'zdjgCodeId': [] if agency is None else [agency], 'searchContent': keyword, 'orderByParam': {'order': '-1', 'sort': ''}, 'pageNum': page, 'pageSize': size})
    if not isinstance(result, dict) or result.get('code') != 200 or type(result.get('total')) is not int or (result['total'] < 0) or (not isinstance(result.get('rows'), list)) or (len(result['rows']) > min(size, max(0, result['total'] - (page - 1) * size))):
        raise ValueError('国家法律法规数据库返回状态或分页结构异常')
    return {**result, 'toolkit_total_unverified': True, 'toolkit_note': '站方可能对检索词分词并按相关性返回结果；实测相同查询更改每页数量时返回的总数可能不一致，故总数未经独立验证，跨请求翻页结果也需核对；score 为站方检索相关性值，同一文书会随请求条件变化，不可跨请求比较；请逐项核对标题、正文及效力状态。'}

def law_detail(id):
    if not re.fullmatch('[a-fA-F0-9]{32}', id):
        raise ValueError('bbbs 必须为 32 位十六进制')
    return get(LAW + '/search/flfgDetails', {'bbbs': id})

def law_enum():
    return get(LAW + '/search/enumData')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('case-list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = sub.add_parser('case-detail')
    q.add_argument('id')
    q = sub.add_parser('law-search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=10)
    q.add_argument('--status', type=int, choices=[1, 2, 3, 4])
    q.add_argument('--range', type=int, choices=[1, 2], default=1)
    q.add_argument('--category', type=int)
    q.add_argument('--agency', type=int)
    q.add_argument('--year', type=int)
    q = sub.add_parser('law-detail')
    q.add_argument('id')
    sub.add_parser('law-enum')
    a = p.parse_args()
    result = {'case-list': lambda: guidance_list(a.page, a.keyword), 'case-detail': lambda: guidance_detail(a.id), 'law-search': lambda: law_search(a.keyword, a.page, a.size, a.status, a.range, a.category, a.agency, a.year), 'law-detail': lambda: law_detail(a.id), 'law-enum': law_enum}[a.cmd]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
