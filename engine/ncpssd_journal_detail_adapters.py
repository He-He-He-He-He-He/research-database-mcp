"""国家哲学社会科学文献中心中文期刊文章公开题录详情。"""
import release_runtime
import re
import requests
URL = 'https://www.ncpssd.cn/articleinfoHandler/getjournalarticletable'

def ncpssd_journal_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[A-Z0-9]{8,40}', record_id):
        raise ValueError('请输入文献中心检索结果中的中文期刊文章编号')
    r = requests.post(URL, json={'lngid': record_id, 'type': '中文期刊文章', 'pageType': '2'}, timeout=20)
    r.raise_for_status()
    out = r.json()
    d = out.get('data')
    if out.get('code') != 200 or not isinstance(d, dict) or d.get('lngid') != record_id or (not d.get('titlec')):
        raise ValueError('未确认题录详情或记录编号')
    return {'source': '国家哲学社会科学文献中心中文期刊文章公开题录', 'source_url': 'https://www.ncpssd.cn/', 'id': record_id, 'title': d.get('titlec'), 'title_english': d.get('titlee'), 'authors': d.get('showwriter'), 'institutions': d.get('showorgan'), 'journal': d.get('mediac'), 'year': d.get('years'), 'volume': d.get('vol'), 'issue': d.get('num'), 'issn': d.get('issn'), 'doi': d.get('doi'), 'keywords': d.get('keywordc'), 'classification': d.get('clazz'), 'note': '仅返回公开题录字段，不请求正文；空值为上游未提供，机构身份与全文权限未验证。'}
