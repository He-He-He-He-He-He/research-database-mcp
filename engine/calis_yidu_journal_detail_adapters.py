"""CALIS e读期刊文章公开题录详情。"""
import release_runtime
import re
import requests
URL = 'https://yidu.calis.edu.cn/prod-api/yidu/resource/getInfo'

def calis_yidu_journal_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{24}', record_id):
        raise ValueError('仅接受 e读期刊文章的24位十六进制编号')
    r = requests.get(URL, params={'ukey': record_id, 'type': 'JNArt'}, timeout=20)
    r.raise_for_status()
    out = r.json()
    if out.get('code') != 200 or not isinstance(out.get('data'), dict):
        raise ValueError('详情查询失败，可能需要验证或登录')
    rows = out['data'].get('concat')
    if not isinstance(rows, list):
        raise ValueError('详情记录缺失')
    matches = [x for x in rows if x.get('ukey') == record_id and x.get('schemacode') == 'JNArt']
    if len(matches) != 1 or not matches[0].get('string_title'):
        raise ValueError('未确认期刊文章编号或题名')
    x = matches[0]
    return {'source': 'CALIS e读期刊文章公开题录', 'source_url': 'https://yidu.calis.edu.cn/', 'id': record_id, 'type': 'JNArt', 'title': x.get('string_title'), 'author': x.get('string_creator'), 'journal': x.get('string_journal_title'), 'year': x.get('string_publishyear'), 'issn': x.get('string_journal_ISSN'), 'keywords': x.get('string_Key'), 'citation': x.get('quote'), 'note': '仅返回公开题录，不获取全文或发起互借；空字段为上游未提供，馆藏与阅读权限未验证。'}
