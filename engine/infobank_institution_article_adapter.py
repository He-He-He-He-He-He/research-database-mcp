"""One institution-authorized Infobank article; no bulk download."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
BASE = 'http://www.bjinfobank.com/'

def article(record_id, database, partition, session=None):
    if not isinstance(record_id, str) or not re.fullmatch('\\d{1,20}', record_id):
        raise ValueError('记录编号无效')
    if not isinstance(database, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', database):
        raise ValueError('数据库标识无效')
    if not isinstance(partition, str) or not re.fullmatch('[A-Za-z0-9_]{1,40}', partition):
        raise ValueError('分区标识无效')
    s = session or requests.Session()
    r = s.get(BASE + 'indexShow.do', params={'method': 'index'}, timeout=20)
    r.raise_for_status()
    params = {'method': 'DataView', 'id': record_id, 'db': database, 'tableName': partition, 'view': 'no', 'str': ''}
    r = s.get(BASE + 'DataList.do', params=params, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    text = p.get_text(' ', strip=True)
    if 'ZJDX' not in text:
        raise RuntimeError('未确认浙江大学机构会话标识')
    crumb = p.select_one('.tictab td')
    body = p.select_one('#text')
    meta = p.select_one('.bmtitle')
    if not crumb or not body or (not meta):
        raise RuntimeError('文章详情或正文未识别')
    title = crumb.get_text(' ', strip=True).split('>>')[-1].strip()
    if not title:
        raise RuntimeError('文章标题缺失')
    vals = {}
    for e in meta.select('.titlespan'):
        v = e.get_text('', strip=True)
        for label, key in [('发布时间：', 'published'), ('来源：', 'original_source'), ('地区分类：', 'region'), ('行业分类：', 'industry')]:
            if v.startswith(label):
                vals[key] = v[len(label):].strip()
    paragraphs = []
    for x in body.children:
        if isinstance(x, NavigableString):
            v = str(x).strip()
        elif isinstance(x, Tag):
            v = x.get_text(' ', strip=True)
        else:
            continue
        if v:
            paragraphs.append(v)
    if not paragraphs:
        raise RuntimeError('正文为空或未授权')
    return {'source': '中国资讯行高校财经数据库', 'institution_marker': 'ZJDX', 'record_id': record_id, 'database': database, 'partition': partition, 'title': title, 'metadata': vals, 'paragraphs': paragraphs, 'note': '机构会话的单篇文章；原站未在正文页回显记录编号，请结合检索题名核对。原站 HTTP 明文，勿提交敏感信息。'}
