"""中国环境监测总站国家地表水水质实时发布，公开网页数据。"""
import release_runtime
import json, re
import requests
from bs4 import BeautifulSoup
BASE = 'https://szzdjc.cnemc.cn:8070'
PAGE = BASE + '/GJZ/Business/Publish/Main.html'
EXPLAIN = BASE + '/GJZ/Business/Publish/Explain.html'

def _request(method, path, **kwargs):
    r = requests.request(method, BASE + path, timeout=25, allow_redirects=False, **kwargs)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 8000000:
        raise ValueError('响应跳转或过大')
    return r

def areas():
    s = _request('GET', '/GJZ/Scripts/Publish/Common.js?v2.1').text
    m = re.search('var\\s+_TopAreaInfo\\s*=\\s*(\\[.*?\\])\\s*;', s, re.S)
    if not m:
        raise ValueError('未识别省份列表')
    return {'source': '中国环境监测总站', 'items': json.loads(m.group(1)), 'source_url': PAGE, 'note': '省份代码为页面公布的筛选项；公开站点数量随运行情况改变。'}

def observations(area='', page=1):
    if not isinstance(area, str) or (area and (not re.fullmatch('\\d{6}', area))):
        raise ValueError('地区应为空或六位地区代码')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码应为1–1000')
    data = {'AreaID': area, 'RiverID': '', 'MNName': '', 'PageIndex': page, 'PageSize': 60, 'action': 'getRealDatas'}
    r = _request('POST', '/GJZ/Ajax/Publish.ashx', data=data, headers={'Referer': BASE + '/GJZ/Business/Publish/RealDatas.html'})
    try:
        j = r.json()
    except ValueError:
        raise ValueError('上游未返回 JSON') from None
    if j.get('result') != 1 or not isinstance(j.get('thead'), list) or (not isinstance(j.get('tbody'), list)):
        raise ValueError('实时数据未返回成功')
    columns = [BeautifulSoup(str(x), 'html.parser').get_text(' ', strip=True) for x in j['thead']]
    rows = []
    for row in j['tbody']:
        if not isinstance(row, list) or len(row) != len(columns):
            raise ValueError('上游数据列数变化')
        cells = []
        for value in row:
            soup = BeautifulSoup(str(value) if value is not None else '', 'html.parser')
            span = soup.find('span')
            raw = span.get('title') if span else None
            cells.append({'display': soup.get_text(' ', strip=True), 'original_note': raw})
        rows.append(cells)
    return {'source': '中国环境监测总站国家地表水自动监测', 'source_url': PAGE, 'explanation_url': EXPLAIN, 'area_code': area, 'page': page, 'page_size': 60, 'reported_records': j.get('records'), 'reported_pages': j.get('total'), 'columns': columns, 'rows': rows, 'note': '页面提供当前自动监测数据，返回行数可能小于每页大小，站点可能变化；时间以原站显示为准，水质类别原始代码需核对发布说明。保留显示值和原始值提示，缺测不作零；不是历史数据库或饮用水安全结论。'}
