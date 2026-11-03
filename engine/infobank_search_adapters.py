"""中国资讯行高校财经数据库题录检索（机构 IP 会话，HTTP）。"""
import release_runtime
import html
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import re
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor
from bs4 import BeautifulSoup
BASE = 'http://www.bjinfobank.com'
DATABASES = {'KX': 'INFOBANK环球商讯库', 'FL': '中国法律法规库', 'HK': '中国经济新闻库', 'BG': '中国商业报告库', 'SS': '中国上市公司文献库', 'TJ': '中国统计数据库', 'JK': '中国医疗健康库'}
HISTORICAL_DATABASES = {'WK': 'English Publications', 'MC': '名词解释库', 'HS': '香港上市公司资料库 (中文)', 'PJ': '中国拟建在建项目数据库', 'QY': '中国企业产品库', 'RW': '中国人物库', 'OG': '中国中央及地方政府机构库'}

class Results(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.in_total = False
        self.total = None
        self.anchor = None
        self.anchor_text = []
        self.bad_rows = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'span' and a.get('class') == 'mlgreen':
            self.in_total = True
        if tag == 'a' and a.get('class') == 'tabListA':
            match = re.match("javascript:openData\\('([^']+)','([^']+)','([^']+)'", a.get('href', ''))
            if match:
                self.anchor = {'title': html.unescape(a.get('title') or ''), 'record_id': match.group(1), 'database': match.group(2), 'partition': match.group(3)}
                self.anchor_text = []
            else:
                self.bad_rows += 1

    def handle_data(self, data):
        if self.in_total and data.strip().isdigit():
            self.total = int(data.strip())
        if self.anchor is not None:
            self.anchor_text.append(data)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.in_total = False
        if tag in ('a', 'td') and self.anchor is not None:
            rendered = ' '.join(''.join(self.anchor_text).split())
            attr = ' '.join(self.anchor['title'].split())
            prefix = rendered.rstrip('.…。 ')
            if tag == 'td' and attr:
                self.anchor['title'] = attr
            elif rendered and (not (attr and attr.startswith(prefix))):
                self.anchor['title'] = rendered
            if self.anchor['title']:
                self.items.append(self.anchor)
            else:
                self.bad_rows += 1
            self.anchor = None
            self.anchor_text = []

def search(keyword, page=1, database='', field='all', historical=False, match='fuzzy'):
    if type(historical) is not bool:
        raise ValueError('历史库开关须为布尔值')
    modes = {'fuzzy': '0', 'any': '1', 'all': '2', 'exclude': '3'}
    if match not in modes:
        raise ValueError('不支持的匹配模式')
    if match != 'fuzzy' and (historical or field != 'title' or database not in (('HK', 'KX', 'FL') if match == 'all' else ('HK',))):
        raise ValueError('该匹配模式仅支持已验证的标题及分库组合')
    if field not in ('all', 'title') or (historical and field != 'all'):
        raise ValueError('不支持的检索字段')
    available = HISTORICAL_DATABASES if historical else DATABASES
    if database not in ('', *available):
        raise ValueError('不支持的分库代码')
    if not keyword.strip() or not 1 <= int(page) <= 400:
        raise ValueError('请输入关键词，页码须在 1–400 范围内')
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    opener.open(BASE + '/indexShow.do?method=index', timeout=20).read()
    params = {'method': 'DataList', 'iw': keyword, 'db': database, 'myorder': 'SUTM', 'selectType': 'selectData', 'search': 'search', 'page': int(page)}
    if field == 'title':
        params.update({'query': 'TI', 'rl': modes[match]})
    if historical:
        params.update({'method': 'DataList_His', 'query': 'all', 'rl': '0'})
        body = opener.open(BASE + '/DataList.do', data=urlencode(params).encode(), timeout=30).read().decode('utf-8', 'replace')
    else:
        body = opener.open(BASE + '/DataList.do?' + urlencode(params), timeout=30).read().decode('utf-8', 'replace')
    if not re.search('ZJDX\\s*(?:&nbsp;|\\s)+欢迎到访资讯行', body):
        raise RuntimeError('未识别浙江大学机构会话，停止查询；请检查机构网络和网站权限')
    if historical and '全部历史库' not in BeautifulSoup(body, 'html.parser').get_text(' ', strip=True):
        raise RuntimeError('未确认站方历史库页面')
    if database:
        selected = BeautifulSoup(body, 'html.parser').select('select[name=db] option[selected]')
        if len(selected) != 1 or selected[0].get('value') != database:
            raise RuntimeError('站方分库选择未正确回显')
    parser = Results()
    parser.feed(body)
    if parser.total is None or parser.bad_rows or (parser.total > 0 and (not parser.items)):
        raise RuntimeError('页面未识别完整查询结果；可能被限制或页面结构变化')
    if database and any((x['database'] != database for x in parser.items)):
        raise RuntimeError('检索结果含其他分库')
    result = {'source': '中国资讯行高校财经数据库', 'keyword': keyword, 'page': int(page), 'total': parser.total, 'items': parser.items, 'scope': '全部更新数据库，全文字段模糊检索；只返回题录标题及记录标识，未验证正文或下载权限', 'note': '该站使用明文 HTTP，检索词和结果可能被网络中间方读取，请勿提交敏感信息。页面显示机构标识并不代表每条正文均有授权。'}
    if database:
        result['database_filter'] = {'code': database, 'name': available[database]}
        result['scope'] = '站方所选分库的全文字段模糊检索；只返回题录标题及记录标识，未验证每条正文或下载权限'
    if historical:
        result['collection'] = 'historical'
        result['scope'] = '站方所选历史库的全文字段模糊检索；只返回题录标题及记录标识，逐条正文及下载权限未核'
        result['note'] += ' 站方未回显页码；历史库资料不应视为现行或最新信息。'
    if field == 'title':
        result['field_requested'] = 'title'
        result['scope'] = ('站方所选分库' if database else '全部更新数据库') + '的标题模糊检索；只返回题录标题及记录标识，正文与下载权限须逐项核验'
        result['note'] += ' 站方未回显标题筛选条件，请核对结果。'
    if match != 'fuzzy':
        result['match_requested'] = match
        result['scope'] = '站方所选分库的标题字词匹配；仅题录，正文和下载权限未验'
        result['note'] += ' 站方未回显字词模式，分词、匹配与结果完整性须核对。'
    return result
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
