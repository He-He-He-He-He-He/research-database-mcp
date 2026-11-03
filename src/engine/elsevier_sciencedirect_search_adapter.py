"""ScienceDirect Search API v2 官方原生 PUT 搜索；仅题录元数据。"""
import release_runtime
import re
import subprocess
import requests
URL = 'https://api.elsevier.com/content/search/sciencedirect'
DOC = 'https://dev.elsevier.com/tecdoc_sdsearch_migration.html'
SERVICE = 'zju-research-toolkit'
ACCOUNT = 'research-toolkit-elsevier'

def _key():
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    return p.stdout.strip()

def search(query, offset=0, limit=5):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('检索词须为 1–250 字单行文本')
    if type(offset) is not int or not 0 <= offset <= 5990 or type(limit) is not int or (not 1 <= limit <= 10):
        raise ValueError('offset 须为 0–5990 的整数，limit 须为 1–10 的整数')
    body = {'qs': query.strip(), 'display': {'offset': offset, 'show': 10}}
    try:
        r = requests.put(URL, json=body, headers={'X-ELS-APIKey': _key(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('ScienceDirect 请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('ScienceDirect API 返回 HTTP ' + str(r.status_code) + '，请检查授权或限额')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('ScienceDirect 未返回 JSON') from None
    if not isinstance(d, dict) or type(d.get('resultsFound')) is not int or d['resultsFound'] < 0:
        raise RuntimeError('ScienceDirect 结果总数异常')
    total = d['resultsFound']
    rows = d.get('results', []) if total == 0 else d.get('results')
    if not isinstance(rows, list) or len(rows) > 10 or any((not isinstance(x, dict) or not isinstance(x.get('title'), str) or (not isinstance(x.get('pii'), str)) for x in rows)):
        raise RuntimeError('ScienceDirect 搜索结果结构异常')
    if total == 0 and rows:
        raise RuntimeError('ScienceDirect 零结果与记录矛盾')
    details = d.get('details')
    if details is not None and (not isinstance(details, dict)):
        raise RuntimeError('ScienceDirect 说明结构异常')
    selected = rows[:limit]
    next_offset = offset + len(selected) if selected and offset + len(selected) < total and (offset + len(selected) <= 5990) else None
    return {'source': 'Elsevier ScienceDirect Search API v2', 'documentation': DOC, 'query': query.strip(), 'offset_requested': offset, 'upstream_page_size': 10, 'upstream_items_received': len(rows), 'truncated': len(rows) > len(selected), 'next_offset': next_offset, 'total_raw': total, 'upstream_message_raw': (details or {}).get('message'), 'items': selected, 'note': '官方原生 PUT 题录搜索；上游响应未回显偏移量。按 next_offset 继续可避免跳过本次截断的记录；实际排序可能随时间变化。上游可能将宽泛检索总数截为 1000000 并要求细化，不应当作精确总数；本机 offset 最多 5990。记录及开放获取标记不代表逐篇订购或全文权限，具体许可应核对。'}

def detail(pii, include_abstract=False):
    if not isinstance(pii, str) or not re.fullmatch('[A-Za-z0-9]{5,40}', pii):
        raise ValueError('PII 须为 5–40 位字母或数字，可使用搜索结果中的 pii')
    if type(include_abstract) is not bool:
        raise ValueError('include_abstract 须为布尔值')
    view = 'META_ABS' if include_abstract else 'META'
    try:
        r = requests.get('https://api.elsevier.com/content/article/pii/' + pii, params={'view': view}, headers={'X-ELS-APIKey': _key(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('ScienceDirect 详情请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('ScienceDirect 详情返回 HTTP ' + str(r.status_code) + '；无法据此确定记录不存在或无权访问')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('ScienceDirect 详情未返回 JSON') from None
    outer = d.get('full-text-retrieval-response') if isinstance(d, dict) else None
    core = outer.get('coredata') if isinstance(outer, dict) else None
    if not isinstance(core, dict) or not isinstance(core.get('pii'), str) or re.sub('[^A-Za-z0-9]', '', core['pii']).upper() != pii.upper() or (not isinstance(core.get('dc:title'), str)):
        raise RuntimeError('ScienceDirect 返回文章 PII 或题名与请求不符')
    fields = ('pii', 'dc:title', 'prism:doi', 'dc:identifier', 'eid', 'prism:publicationName', 'prism:aggregationType', 'pubType', 'prism:issn', 'prism:volume', 'prism:startingPage', 'prism:endingPage', 'prism:pageRange', 'prism:coverDate', 'prism:coverDisplayDate', 'prism:copyright', 'prism:publisher', 'dc:creator', 'openaccess', 'openaccessArticle', 'openaccessType', 'openArchiveArticle', 'openaccessUserLicense', 'dcterms:subject')
    if include_abstract:
        fields += ('dc:description',)
    return {'source': 'Elsevier Article Retrieval API（' + view + ' 视图）', 'documentation': 'https://dev.elsevier.com/sd_api_spec.html', 'pii_requested': pii, 'coredata': {k: core[k] for k in fields if k in core}, 'scopus_id_raw': outer.get('scopus-id'), 'scopus_eid_raw': outer.get('scopus-eid'), 'pubmed_id_raw': outer.get('pubmed-id'), 'note': '官方 ' + view + ' 视图，返回选择的原始元数据' + ('及可能提供的摘要' if include_abstract else '') + '，不取全文或结构；缺少摘要不代表没有摘要。PII 按字母数字规范化核对。开放获取标志不证明浙大逐篇订购或全文权限。'}

def serial(issn):
    if not isinstance(issn, str) or not re.fullmatch('\\d{4}-?\\d{3}[\\dXx]', issn):
        raise ValueError('ISSN 格式须为 0000-0000 或 00000000（末位可为 X）')
    code = issn.replace('-', '').upper()
    try:
        r = requests.get('https://api.elsevier.com/content/serial/title/issn/' + code, headers={'X-ELS-APIKey': _key(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Elsevier 期刊请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Elsevier 期刊接口返回 HTTP ' + str(r.status_code) + '；无法据此判断期刊是否存在或学校权限')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('Elsevier 期刊接口未返回 JSON') from None
    result = d.get('serial-metadata-response') if isinstance(d, dict) else None
    entries = result.get('entry') if isinstance(result, dict) else None
    if not isinstance(entries, list) or not entries:
        raise RuntimeError('Elsevier 期刊响应缺少记录')
    items = []
    fields = ('dc:title', 'dc:publisher', 'coverageStartYear', 'coverageEndYear', 'prism:aggregationType', 'source-id', 'prism:issn', 'prism:eIssn', 'openaccess', 'openaccessArticle', 'openArchiveArticle', 'openaccessType', 'openaccessStartDate', 'subject-area', 'SNIPList', 'SJRList', 'citeScoreYearInfoList')
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('dc:title'), str):
            raise RuntimeError('Elsevier 期刊记录缺少题名')
        ids = [re.sub('[^0-9Xx]', '', str(entry.get(k, ''))).upper() for k in ('prism:issn', 'prism:eIssn')]
        if code not in ids:
            raise RuntimeError('Elsevier 期刊返回 ISSN 与请求不一致')
        items.append({k: entry[k] for k in fields if k in entry})
    return {'source': 'Elsevier Serial Title Metadata API', 'documentation': 'https://dev.elsevier.com/sd_api_spec.html', 'issn_requested': issn, 'items': items, 'note': '按原站返回的印刷或电子 ISSN 核对；指标及年份为原始值。CiteScore、SJR、SNIP 并非 JCR 影响因子，开放获取标记与索引覆盖年份不等于浙大订购、逐篇全文权限或期刊质量结论。'}

def book(isbn):
    if not isinstance(isbn, str) or not re.fullmatch('(?:[0-9]{9}[0-9Xx]|[0-9]{13})', isbn):
        raise ValueError('ISBN 须为不含连字符的 10 位或 13 位编号')
    code = isbn.upper()
    try:
        r = requests.get('https://api.elsevier.com/content/nonserial/title/isbn/' + code, headers={'X-ELS-APIKey': _key(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Elsevier 图书请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Elsevier 图书接口返回 HTTP ' + str(r.status_code) + '；无法据此确定图书不存在或学校权限')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('Elsevier 图书接口未返回 JSON') from None
    result = d.get('nonserial-metadata-response') if isinstance(d, dict) else None
    entries = result.get('entry') if isinstance(result, dict) else None
    if not isinstance(entries, list) or not entries:
        raise RuntimeError('Elsevier 图书响应缺少记录')
    items = []
    fields = ('dc:title', 'prism:edition', 'prism:aggregationType', 'dc:publisher', 'prism:isbn', 'subject-area', 'authors', 'editors', 'description')
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('dc:title'), str) or (not isinstance(entry.get('prism:isbn'), str)) or (entry['prism:isbn'].replace('-', '').upper() != code):
            raise RuntimeError('Elsevier 图书返回 ISBN 或题名与请求不符')
        items.append({k: entry[k] for k in fields if k in entry})
    return {'source': 'Elsevier Nonserial Title Metadata API', 'documentation': 'https://dev.elsevier.com/documentation/NonSerialTitleAPI.wadl', 'isbn_requested': isbn, 'items': items, 'note': '原站 ISBN 元数据，保留原始版次、作者、出版社和描述；条目可见不代表学校订购、图书全文或其他版本权限。'}
