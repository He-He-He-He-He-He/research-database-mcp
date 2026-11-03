"""Official Clarivate Starter API; credentials stay in macOS Keychain."""
import release_runtime
import subprocess, requests, re
from datetime import date
URL = 'https://api.clarivate.com/apis/wos-starter/v1/documents'
DOC = 'https://developer.clarivate.com/apis/wos-starter'
DATABASES = {'WOS', 'BIOABS', 'BCI', 'BIOSIS', 'CCC', 'DIIDW', 'DRCI', 'MEDLINE', 'ZOOREC', 'PPRN', 'WOK'}

def search(query, db='WOS', page=1, limit=5, *, sort_field='', modified_time_span='', tc_modified_time_span=''):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError('请输入1—1000字符的官方查询表达式')
    if db not in DATABASES or isinstance(page, bool) or (not isinstance(page, int)) or (page < 1) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 50):
        raise ValueError('数据库、页码或条数无效')
    if sort_field and (not isinstance(sort_field, str) or not re.fullmatch('(?:LD|PY|RS|TC)\\+[AD](?:,(?:LD|PY|RS|TC)\\+[AD])*', sort_field)):
        raise ValueError('排序格式如 PY+D 或 TC+D')
    for span in (modified_time_span, tc_modified_time_span):
        if span:
            if not isinstance(span, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}\\+\\d{4}-\\d{2}-\\d{2}', span):
                raise ValueError('修改日期范围须为 YYYY-MM-DD+YYYY-MM-DD')
            first, last = span.split('+')
            try:
                first, last = (date.fromisoformat(first), date.fromisoformat(last))
            except ValueError:
                raise ValueError('修改日期范围无效') from None
            if first > last:
                raise ValueError('修改日期起点不得晚于终点')
            if db == 'WOK':
                raise ValueError('WOK 全库不支持修改日期筛选')
    p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'research-toolkit-wos-starter', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=20)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('钥匙串没有可用的 WOS Starter 密钥')
    params = {'q': query.strip(), 'db': db, 'page': page, 'limit': limit}
    if sort_field:
        params['sortField'] = sort_field
    if modified_time_span:
        params['modifiedTimeSpan'] = modified_time_span
    if tc_modified_time_span:
        params['tcModifiedTimeSpan'] = tc_modified_time_span
    try:
        r = requests.get(URL, params=params, headers={'X-ApiKey': p.stdout.strip()}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('Clarivate 网络请求失败：' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Clarivate 接口返回 HTTP ' + str(r.status_code) + '；请核对查询、配额与当前订阅范围')
    try:
        body = r.json()
    except ValueError:
        raise RuntimeError('Clarivate 返回非 JSON') from None
    if not isinstance(body, dict) or not isinstance(body.get('hits'), list) or (not isinstance(body.get('metadata'), dict)):
        raise RuntimeError('Clarivate 响应结构异常')
    return {'source': 'Clarivate Web of Science Starter API', 'documentation': DOC, 'database': db, 'query': query.strip(), 'sort_field': sort_field or None, 'modified_time_span': modified_time_span or None, 'tc_modified_time_span': tc_modified_time_span or None, 'metadata': body['metadata'], 'items': body['hits'], 'note': '返回官方原始题录和可用引文信息；修改时间为记录或引文更新日期，不是发表日期。不同数据库、引文及全文权限取决于实际订阅。单次请求，未自动限速或重试；API与机构合同及第三方AI处理许可仍适用。'}
