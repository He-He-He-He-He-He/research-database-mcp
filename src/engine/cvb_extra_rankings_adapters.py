"""中国视听大数据官网季度榜及 IPTV 点播周榜。"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://www.cavbd.cn/prod-api/cvb/'
TYPES = {1: '央视黄金时段收官电视剧收视率', 2: '央视晚间时段首播文艺节目收视率', 3: '地方卫视黄金时段收官电视剧收视率', 4: '地方卫视晚间时段首播文艺节目收视率'}

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('CVB 查询失败: ' + p.stderr.strip())
    try:
        r = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError('返回非 JSON，可能访问受限或网页变化') from exc
    if r.get('msg') != '查询成功' or 'rows' not in r:
        raise RuntimeError('上游响应异常: ' + str(r.get('msg')))
    return {'source': url, **r}

def quarterly_dates(category):
    category = int(category)
    if category not in TYPES:
        raise ValueError('仅支持已核实分类 1—4')
    return {'category_label': TYPES[category], **_get('quarterlyrankings/quarterly_date_list', {'pageSize': 10, 'type': category})}

def quarterly(category, period):
    category = int(category)
    if category not in TYPES or not re.fullmatch('\\d{8}-\\d{8}', str(period)):
        raise ValueError('类别或期次无效')
    return {'category_label': TYPES[category], **_get('quarterlyrankings/list', {'type': category, 'date': period})}

def iptv_dates():
    return _get('iptv/datelist')

def iptv(period, kind='电视剧', page=1, size=20):
    page, size = (int(page), int(size))
    if kind not in ('电视剧', '文艺节目') or not re.fullmatch('\\d{8}-\\d{8}', str(period)) or page < 1 or (not 1 <= size <= 100):
        raise ValueError('节目类型、期次或分页无效')
    return _get('iptv/list', {'weekRange': period, 'type': kind, 'pageNum': page, 'pageSize': size})
