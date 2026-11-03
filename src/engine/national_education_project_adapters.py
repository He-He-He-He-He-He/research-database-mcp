"""全国教育科学规划官方立项和结项查询。"""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
BASE = 'https://onsgep.moe.edu.cn/api.php'
FIELDS = {'立项': {'ketipizhunhao', 'leibie', 'ketimingcheng', 'xingming', 'gongzuodanwei', 'lixiangniandu'}, '结项': {'ketipizhunhao', 'ketimingcheng', 'ketifuzeren', 'gongzuodanwei', 'zhengshuhao', 'jiandingjieguo', 'shangwangshijian'}}
TOOLS = {'立项': 'lixiangshuju', '结项': 'ketijianding'}

def _fetch(query):
    url = BASE + '?' + urlencode(query)
    obj = json.loads(release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig'))
    if obj.get('code') != 200 or not isinstance(obj.get('data'), list):
        raise ValueError('上游返回异常')
    return obj

def education_project_metadata(kind='立项'):
    if kind not in TOOLS:
        raise ValueError('kind 须为立项或结项')
    obj = _fetch({'tool': TOOLS[kind]})
    return {'kind': kind, 'parameters': obj.get('parameters', {}), 'source_url': 'https://onsgep.moe.edu.cn/xmgl/xmcx'}

def education_project_search(kind='立项', page=1, **filters):
    if kind not in TOOLS:
        raise ValueError('kind 须为立项或结项')
    page = int(page)
    if not 1 <= page <= 10000:
        raise ValueError('页码必须在 1—10000')
    if set(filters) - FIELDS[kind]:
        raise ValueError('不支持的筛选字段：' + ', '.join(sorted(set(filters) - FIELDS[kind])))
    fields = {k: v for k, v in filters.items() if v is not None and str(v).strip()}
    if not fields:
        raise ValueError('至少提供一个非空查询字段')
    obj = _fetch({'tool': TOOLS[kind], 'page': page, 'per_page': 10, **fields})
    return {'kind': kind, 'page': page, 'pagination': obj.get('pagination', {}), 'results': obj['data'], 'source_url': 'https://onsgep.moe.edu.cn/xmgl/xmcx'}
