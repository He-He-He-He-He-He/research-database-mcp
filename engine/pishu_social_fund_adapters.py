"""皮书平台国家社科基金项目数据库单页项目名称检索。"""
import release_runtime
import time
import requests
URL = 'https://www.pishu.com.cn/skwx_jj/front/projectFund/list'
_last_request = 0.0

def pishu_social_fund_search(keyword, page=1, page_size=10, *, institution='', subject=''):
    global _last_request
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    if not isinstance(institution, str) or not isinstance(subject, str) or len(institution) > 100 or (len(subject) > 100):
        raise ValueError('机构和学科均须不超过100字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页1至20条')
    delay = 1 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    r = requests.get(URL, params={'pageIndex': page - 1, 'pageSize': page_size, 'XmName': keyword.strip(), 'Gzdw': institution.strip(), 'XkTye': subject.strip(), 'sortField': 'LxTime', 'sortOrder': 'desc'}, headers={'Accept': 'application/json'}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data.get('total'), int) or not isinstance(data.get('data'), list):
        raise ValueError('未识别平台返回的项目结果')
    items = []
    for x in data['data']:
        if not x.get('XmName') or not x.get('XmNum'):
            raise ValueError('项目名称或批准号缺失')
        items.append({'project_number': x.get('XmNum'), 'project_name': x.get('XmName'), 'subject': x.get('XkTye'), 'category': x.get('XmTypeFirst'), 'subcategory': x.get('XmTypeSecond'), 'leader': x.get('XmLeader'), 'institution': x.get('Gzdw'), 'province': x.get('Province'), 'year': x.get('LxTimeYear'), 'month': x.get('LxTimeMonth'), 'day': x.get('LxTimeDay'), 'result_name': x.get('ResultsName'), 'result_type': x.get('ResultsShape'), 'result_level': x.get('ResultsLevel')})
    return {'source': '社会科学文献出版社皮书平台国家社科基金项目数据库', 'source_url': 'https://www.pishu.com.cn/skwx_ps/v/skjj_index/14/index.shtml', 'keyword': keyword.strip(), 'institution_filter': institution.strip(), 'subject_filter': subject.strip(), 'total': data['total'], 'page': page, 'items': items, 'note': '项目名称及可选机构、学科字段查询；这是出版社平台整理数据，非政府原始数据库，项目状态和最新信息应核对官方公布。'}
