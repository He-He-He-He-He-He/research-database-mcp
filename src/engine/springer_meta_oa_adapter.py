"""Springer Nature Meta API v2：仅输出本页标为开放获取的书目字段。"""
import release_runtime
import re
import subprocess
import requests
URL = 'https://api.springernature.com/meta/v2/json'
DOC = 'https://dev.springernature.com/docs/supported-query-params/'
FIELDS = ('identifier', 'doi', 'title', 'creators', 'publicationName', 'publicationDate', 'onlineDate', 'publicationType', 'contentType', 'language', 'openaccess', 'publisher', 'publisherName', 'issn', 'eIssn', 'volume', 'number', 'startingPage', 'endingPage', 'article-number', 'journalId', 'copyright')

def search(query, start=1, limit=20):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('查询须为 1–250 字单行文本')
    if type(start) is not int or not 1 <= start <= 9981 or type(limit) is not int or (not 1 <= limit <= 20):
        raise ValueError('start 须为 1–9981，limit 须为 1–20')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'research-toolkit-springer-meta', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        raise RuntimeError('Springer 钥匙串读取超时') from None
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Springer Meta API 密钥')
    try:
        r = requests.get(URL, params={'api_key': p.stdout.strip(), 'q': query.strip(), 'p': 20, 's': start}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('Springer API 请求失败：' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Springer API 返回 HTTP ' + str(r.status_code) + '；可能与查询条件、配额或订阅有关')
    try:
        o = r.json()
    except ValueError:
        raise RuntimeError('Springer API 返回非 JSON') from None
    records = o.get('records') if isinstance(o, dict) else None
    results = o.get('result') if isinstance(o, dict) else None
    if not isinstance(records, list) or len(records) > 20 or any((not isinstance(x, dict) for x in records)) or (not isinstance(results, list)) or (len(results) != 1) or (not isinstance(results[0], dict)):
        raise RuntimeError('Springer API 响应结构异常')
    result = results[0]
    try:
        actual = int(result['start'])
        total = int(result['total'])
        displayed = int(result['recordsDisplayed'])
    except (KeyError, ValueError, TypeError):
        raise RuntimeError('Springer API 分页信息异常') from None
    if actual != start or total < 0 or displayed != len(records):
        raise RuntimeError('Springer API 返回起始位置或条数不一致')
    if any((x.get('openaccess') == 'true' and (not x.get('title') or not x.get('identifier')) for x in records)):
        raise RuntimeError('Springer 开放记录缺少标题或标识')
    oa = [{k: x[k] for k in FIELDS if k in x} for x in records if x.get('openaccess') == 'true']
    return {'source': 'Springer Nature Meta API v2', 'documentation': DOC, 'query': query.strip(), 'start': start, 'upstream_total_all_raw': result['total'], 'upstream_records_received': len(records), 'openaccess_records_on_page': len(oa), 'truncated': len(oa) > limit, 'items': oa[:limit], 'note': '上游按每次 20 条检索所有匹配，本机仅输出当前页原始 openaccess=true 的记录及选定书目字段，不输出摘要或非开放记录；总数是全部匹配，不是开放获取总数。空页不能证明没有开放记录；如本页开放记录多于 limit，需增大 limit 查看。开放标志不等于授予全部 AI 使用权限，具体作品许可和接口协议仍适用。'}
