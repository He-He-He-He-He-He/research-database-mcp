"""国研网教育版校园 IP 单篇文章详情。"""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
from drcnet_ip_catalog_adapter import AUTH
DETAIL = 'https://user.drcnet.com.cn/userapi/loginController/commonUserDocById'

def article(doc_id, leaf_id, channel_id, expected_title):
    ids = [str(x) for x in (doc_id, leaf_id, channel_id)]
    if any((not re.fullmatch('[0-9]{1,12}', x) for x in ids)):
        raise ValueError('文章、栏目及频道编号均须为 1–12 位数字')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供检索结果中的完整标题以核对文章')
    doc_id, leaf_id, channel_id = ids
    ref = f'https://d.drcnet.com.cn/?docid={doc_id}&leafid={leaf_id}&chnid={channel_id}'
    with requests.Session() as session:
        r = session.get(AUTH, params={'flag': 'initp'}, timeout=20)
        r.raise_for_status()
        raw = r.text.strip()
        if raw.startswith('(') and raw.endswith(')'):
            raw = raw[1:-1]
        try:
            identity = json.loads(raw)
        except ValueError:
            raise RuntimeError('未识别学校登录响应') from None
        if identity.get('UserName') != '浙江大学图书馆' or identity.get('IsAdvIP') is not True or identity.get('Logined') != 1:
            raise RuntimeError('未确认浙江大学图书馆校园 IP 授权')
        r = session.get(DETAIL, params={'docId': doc_id, 'leafId': leaf_id, 'chnid': channel_id}, headers={'X-Referer': ref}, timeout=30)
        r.raise_for_status()
        try:
            body = r.json()
        except ValueError:
            raise RuntimeError('文章详情未返回 JSON') from None
    data = body.get('data') if isinstance(body, dict) and body.get('code') == 0 else None
    if not isinstance(data, dict):
        raise RuntimeError('国研网未返回有效文章详情')
    doc = data.get('doc')
    if not isinstance(doc, dict) or doc.get('title') != expected_title.strip() or (not re.fullmatch('[A-Za-z0-9]+_' + re.escape(doc_id), str(doc.get('code', '')))):
        raise RuntimeError('返回的文章编号或标题与请求不一致')
    if data.get('hasRight') is not True:
        raise RuntimeError('站方未确认本篇文章读取权限')
    content = doc.get('content')
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError('站方未返回本篇正文')
    soup = BeautifulSoup(content, 'html.parser')
    for node in soup(['script', 'style']):
        node.decompose()
    text = soup.get_text('\n', strip=True)
    if not text:
        raise RuntimeError('未能从站方正文提取文字')
    return {'source': '国研网教育版', 'institution': '浙江大学图书馆（校园 IP）', 'article_code': doc.get('code'), 'title': doc.get('title'), 'author': doc.get('author'), 'publication': doc.get('source'), 'date': doc.get('deliveddate'), 'has_right': True, 'text': text, 'image_count': len(soup.find_all('img')), 'table_count': len(soup.find_all('table')), 'note': '单篇权限由站方返回；正文为 HTML 提取的纯文字，图片、表格结构和排版未保留，请以原文为准。'}
