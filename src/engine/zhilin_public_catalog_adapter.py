"""知领政策库公开标题检索结果，仅读取元数据。"""
import release_runtime
import html
import re
import requests
from urllib.parse import urlsplit, parse_qs
BASE = 'https://policy.ckcest.cn'

def search(keyword, page=1, limit=5, include_context=False):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or re.search('[=\\r\\n\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为1–100字单行文本且不含等号')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码须为1–100')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页数量须为1–10')
    if not isinstance(include_context, bool):
        raise ValueError('include_context 须为布尔值')
    q = keyword.strip()
    with requests.Session() as session:
        r = session.get(BASE + '/search', params={'policyType': '', 'shortname': 'TI', 'word': q}, timeout=20)
        r.raise_for_status()
        payload = {'secondSearchExpress': 'TI=' + q, 'page': page, 'cnt': limit, 'type': ['1005']}
        r = session.post(BASE + '/data/es/search', json=payload, timeout=30)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('知领未返回 JSON') from None
    d = j.get('datas') if isinstance(j, dict) else None
    if not isinstance(d, dict) or not isinstance(d.get('records'), list) or d.get('current') != page or (d.get('size') != limit) or (not isinstance(j.get('total'), int)) or (len(d['records']) > limit):
        raise RuntimeError('知领检索响应结构或页码异常')
    items = []
    for x in d['records']:
        if not isinstance(x, dict) or not isinstance(x.get('_id'), str) or (not re.fullmatch('[0-9a-fA-F]{32}', x['_id'])) or (not isinstance(x.get('title'), str)):
            raise RuntimeError('结果缺少标题或编号')
        title = html.unescape(re.sub('</?em>', '', x['title']))
        item = {'id': x['_id'], 'title': title, 'type': x.get('policy_type'), 'issuer': x.get('source_organization'), 'publish_time_utc': x.get('publish_date'), 'level': x.get('level_name'), 'url': BASE + '/detail/' + x['_id'] + '.html'}
        if include_context:
            chain = x.get('detail_url')
            origin = None
            if isinstance(chain, str):
                parts = urlsplit(chain)
                if parts.scheme == 'https' and parts.hostname == 'prod.ckcest.cn' and (parts.path == '/direct/chain'):
                    found = parse_qs(parts.query).get('url', [])
                    if len(found) == 1 and urlsplit(found[0]).scheme in ('http', 'https'):
                        origin = found[0]
            item.update({'source_url_raw': origin, 'source_domains_raw': x.get('datasource'), 'document_number_raw': x.get('file_number'), 'abstract_raw': x.get('_abstract'), 'keywords_raw': x.get('keywords')})
        items.append(item)
    return {'source': '知领政策库公开题录', 'query': q, 'field': '标题', 'page': page, 'page_size': limit, 'total': j['total'], 'items': items, 'note': '未登录公开检索，含政策文件、解读、讲话等；来源链接和摘要为站方提供，摘要可能截断，未逐项核验链接、正文及法律效力。UTC 时间需按中国时区核对，机构身份未验证。' if include_context else '未登录会话实测的标题元数据，含政策文件、解读、讲话等，不能视为全部现行法规；UTC 时间需按中国时区核对，机构授权、正文及效力未验证。'}
