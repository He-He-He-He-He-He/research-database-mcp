"""浙江大学中国历代墓志数据库：题名分页及题录详情；不获取拓片图像。"""
import release_runtime
import json, re, argparse
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zju_tomb_api import BASE, LIBS, Parser
from zju_tomb_categories_adapter import _validate_page

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('题名须为 1–100 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    p = {'tag': '3', 'dynasty': '', 'stoneType': '', 'subLibType': ','.join(LIBS), 'smSearType': '0', 'smSearchSelect': 'title', 'smInputText': keyword.strip(), 'aSearchType1': '0', 'aSearchSelect1': '', 'aInputText1': '', 'andOr1': '0', 'aSearchType2': '0', 'aSearchSelect2': '', 'aInputText2': '', 'andOr2': '0', 'aSearchType3': '0', 'aSearchSelect3': '', 'aInputText3': '', 'andOr3': '0', 'aSearchType4': '0', 'aSearchSelect4': '', 'aInputText4': '', 'orderField': '', 'orderType': '0', 'pageSize': '15', 'pageNumber': str(page)}
    with urlopen(BASE + 'stone/list?' + urlencode(p), timeout=20) as r:
        html = r.read().decode('utf-8')
    parser = Parser()
    parser.feed(html)
    text = ''.join(parser.text)
    total_match = re.search('記錄數\\s*:\\s*(\\d+)', text)
    pg = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*頁', text)
    if not total_match or not pg:
        soup = BeautifulSoup(html, 'html.parser')
        if page == 1 and soup.title and (soup.title.get_text(' ', strip=True) == '浙大墓志库 - 墓志列表') and ('未找到任何数据' in soup.get_text(' ', strip=True)) and (not parser.rows):
            return {'source': '浙江大学中国历代墓志数据库', 'query': keyword.strip(), 'field': '题名', 'page': 1, 'total': 0, 'pages': 0, 'items': [], 'note': '原站明确显示未找到数据；上游 HTTP 明文，勿输入敏感词。'}
        raise RuntimeError('无法验证结果页或页码，可能超出范围或网站变化')
    if int(pg.group(1)) != page:
        raise RuntimeError('无法验证结果页或页码，可能超出范围或网站变化')
    total = int(total_match.group(1))
    pages = int(pg.group(2))
    _validate_page(total, pages, page, parser.rows)
    return {'source': '浙江大学中国历代墓志数据库', 'query': keyword.strip(), 'field': '题名', 'page': page, 'total': total, 'pages': pages, 'items': parser.rows, 'note': '单页结果；上游 HTTP 明文，勿输入敏感词。原站可能列出重复条目，未去重。'}

def detail(stone_id, rubbing_id):
    for x in (stone_id, rubbing_id):
        if not isinstance(x, str) or not re.fullmatch('[0-9a-fA-F]{32}', x):
            raise ValueError('编号须为 32 位十六进制')
    stone_id = stone_id.lower()
    rubbing_id = rubbing_id.lower()
    url = BASE + 'stone/detail?' + urlencode({'id': stone_id, 'rubbingId': rubbing_id})
    with urlopen(url, timeout=20) as r:
        html = r.read().decode('utf-8')
    s = BeautifulSoup(html, 'html.parser')
    fields = []
    for table in s.select('table.m-table-c1'):
        if 'm-table' in (table.get('class') or []):
            continue
        for tr in table.find_all('tr'):
            cells = tr.find_all('td', recursive=False)
            if len(cells) == 2:
                fields.append({'label': cells[0].get_text(' ', strip=True), 'value': cells[1].get_text(' ', strip=True)})
    if not any((x['label'] == '自擬題名' and x['value'] for x in fields)):
        raise RuntimeError('未识别题录详情或记录无权访问')
    return {'source': '浙江大学中国历代墓志数据库', 'record_url': url, 'fields': fields, 'note': '返回网页显示题录字段，空字段保留；不获取图像及全文，不保证拓片访问权限。原站 HTTP 明文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd', required=True)
    x = sp.add_parser('search')
    x.add_argument('keyword')
    x.add_argument('--page', type=int, default=1)
    x = sp.add_parser('detail')
    x.add_argument('stone_id')
    x.add_argument('rubbing_id')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page) if a.cmd == 'search' else detail(a.stone_id, a.rubbing_id), ensure_ascii=False, indent=2))
