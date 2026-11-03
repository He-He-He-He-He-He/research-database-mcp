"""全国公共资源交易平台数据服务：主体、成交项目及公告详情。"""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.ggzy.gov.cn'

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    proc = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('全国公共资源交易平台请求失败: ' + proc.stderr.strip())
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError('平台返回非 JSON 内容，可能是访问限制或服务变更') from exc
    if not data.get('success') or data.get('code') != 200:
        raise RuntimeError('平台返回错误: ' + str(data.get('message') or data.get('code')))
    return data

def _page(page, size):
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量须为 1—100')
    return {'pageNo': page, 'pageSize': size}

def entities(keyword, page=1, size=10):
    """按主体名称或统一社会信用代码检索；返回平台原始 JSON。"""
    if not keyword or not keyword.strip():
        raise ValueError('请输入主体名称或统一社会信用代码')
    return _get('/yjcx/index/search', {'keyword': keyword, **_page(page, size)})

def awards(uniscid, page=1, size=10, category=''):
    """按统一社会信用代码分页查询成交；category 为平台原始类别代码。"""
    if not uniscid or not uniscid.strip():
        raise ValueError('请输入统一社会信用代码')
    if category not in ('', '01', '02', '03', '04', '0501', '0502'):
        raise ValueError('未知类别代码')
    return _get('/yjcx/index/bid_list', {'uniscid': uniscid, 'tos': category, **_page(page, size)})

def announcement(record_id):
    """按成交记录 ID 获取公告原始详情，content 可能为 HTML 或 JSON。"""
    if not record_id or not record_id.strip():
        raise ValueError('请输入记录 ID')
    return _get('/yjcx/index/bid_show', {'id': record_id})

def counts():
    """平台当前汇总数字，代表平台显示口径而非全国交易总量。"""
    return _get('/yjcx/index/index')
