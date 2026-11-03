"""华艺公开学位论文题录与摘要；不表示学校订购或全文权限。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
_BAD = re.compile('(?:https?://|www\\.|(?:token|session|api[_-]?key)\\s*=)', re.I)
_FIELDS = ('citation_title', 'citation_author', 'citation_journal_title', 'citation_date', 'citation_firstpage', 'citation_lastpage', 'citation_doi', 'citation_keywords', 'citation_abstract')

def detail(doc_id):
    if not isinstance(doc_id, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{1,99}', doc_id):
        raise ValueError('论文 ID 格式无效')
    try:
        r = requests.get('https://www.airitilibrary.cn/Article/Detail', params={'DocID': doc_id}, timeout=20)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError('华艺公开详情请求失败') from exc
    if len(r.content) > 5000000:
        raise RuntimeError('华艺详情响应过大')
    soup = BeautifulSoup(r.content, 'html.parser')
    header = soup.select_one('#Detail_TitleandAuthor_Anchor')
    if doc_id not in r.text or not header or '学位论文' not in header.get_text(' ', strip=True):
        raise ValueError('论文不存在或详情类型、编号未确认')
    record = {'id': doc_id}
    omitted = []
    for name in _FIELDS:
        raw = [m.get('content') for m in soup.find_all('meta', attrs={'name': name})]
        vals = []
        for value in raw:
            if isinstance(value, str) and (not _BAD.search(value)):
                vals.append(value)
            else:
                omitted.append(name)
        record[name] = vals if name == 'citation_author' else vals[0] if vals else None
    if not record['citation_title']:
        raise ValueError('论文详情缺少题名')
    if omitted:
        record['source_fields_omitted'] = sorted(set(omitted))
    return {'source': '华艺公开学位论文详情', 'record': record, 'note': '匿名公开题录和摘要；原站 citation 字段原样保留，不代表学校订购或全文权限。'}
