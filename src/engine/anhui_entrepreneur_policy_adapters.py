"""安徽人社厅创业服务云平台的省级政策文件检索。"""
import release_runtime
import re
import requests
BASE = 'https://www.ahcy.gov.cn/api-manage/v2/front/zctPolicy/'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    params = {'pageNum': page, 'pageSize': 12, 'type': 'D4F6C59F-2C9F-4A7E-8F57-1BD696F5C010', 'title': keyword.strip(), 'place': '', 'province': 'FA0111C0-B6FD-4747-9AFE-E9387F1E5D15', 'city': '', 'district': '', 'provinceDisplay': 1, 'executiveLevel': 1, 'policyType': ''}
    r = requests.get(BASE + 'policyListPage', params=params, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 0:
        raise RuntimeError('官方服务报错')
    obj = d.get('obj', {})
    rows = obj.get('content')
    total = obj.get('totalCount')
    if not isinstance(rows, list) or not isinstance(total, int) or total < 0:
        raise RuntimeError('官方响应结构异常')
    if not rows and (page - 1) * 12 < total:
        raise RuntimeError('返回总数与页内结果不一致')
    return {'source': '安徽省创业服务云平台省级政策文件', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': rows, 'notice': '创业服务平台汇集的省级政策文件，可能含征求意见稿等，非省内全量法规；标题高亮含 HTML。'}

def detail(policy_id):
    if not isinstance(policy_id, str) or not re.fullmatch('[0-9a-fA-F-]{32,36}', policy_id):
        raise ValueError('无效的政策编号')
    r = requests.get(BASE + 'getZctPolicyInfo', params={'id': policy_id}, timeout=20)
    r.raise_for_status()
    d = r.json()
    obj = d.get('obj')
    if d.get('code') != 0 or not isinstance(obj, dict) or obj.get('baseId') != policy_id or (not isinstance(obj.get('content'), str)) or (not obj['content']):
        raise RuntimeError('官方详情缺失或编号不匹配')
    return {'source': '安徽省创业服务云平台', 'item': obj, 'notice': 'content 为平台返回的原始 HTML，格式可能不规范；不是法律效力判断，需核对发布机关和原文。'}
