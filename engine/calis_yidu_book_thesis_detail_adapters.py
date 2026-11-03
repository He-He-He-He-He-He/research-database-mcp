"""CALIS e读图书及学位论文公开题录详情。"""
import release_runtime
import re
import requests
URL = 'https://yidu.calis.edu.cn/prod-api/yidu/resource/getInfo'

def calis_yidu_book_thesis_detail(record_id, resource_type):
    if resource_type not in ('book', 'etd'):
        raise ValueError('类型仅支持 book（图书）或 etd（学位论文）')
    if not isinstance(record_id, str) or not re.fullmatch('[A-Za-z0-9+/=_-]{1,160}', record_id):
        raise ValueError('记录编号格式无效')
    r = requests.get(URL, params={'ukey': record_id, 'type': resource_type}, timeout=20)
    r.raise_for_status()
    out = r.json()
    if out.get('code') != 200 or not isinstance(out.get('data'), dict):
        raise ValueError('详情查询失败，可能需要登录或验证')
    rows = out['data'].get('concat')
    if not isinstance(rows, list):
        raise ValueError('详情记录缺失')
    matches = [x for x in rows if x.get('ukey') == record_id and x.get('schemacode') == resource_type]
    if len(matches) != 1 or not matches[0].get('string_title'):
        raise ValueError('未确认题名、记录编号和类型')
    x = matches[0]
    return {'source': 'CALIS e读图书/学位论文公开题录', 'source_url': 'https://yidu.calis.edu.cn/', 'id': record_id, 'type': resource_type, 'title': x.get('string_title'), 'author': x.get('string_creator'), 'publisher': x.get('string_publisher'), 'year': x.get('string_publishyear'), 'isbn': x.get('string_ISBN'), 'degree_grantor': x.get('string_grantor'), 'keywords': x.get('string_Key'), 'citation': x.get('quote'), 'note': '只返回公开题录，不获取正文或请求互借；空值为上游未提供，馆藏和访问权限未验证。'}
