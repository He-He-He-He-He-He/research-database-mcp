"""Elsevier Scopus Search API using the locally saved application key."""
import release_runtime
import re, subprocess, requests
from urllib.parse import quote, urlsplit, parse_qs
URL = 'https://api.elsevier.com/content/search/scopus'
DOC = 'https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl'

def search(query, start=0, count=5):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError('请输入1—1000字符的Scopus查询表达式')
    if isinstance(start, bool) or not isinstance(start, int) or (not 0 <= start <= 5000) or isinstance(count, bool) or (not isinstance(count, int)) or (not 1 <= count <= 25):
        raise ValueError('start须为0—5000，count须为1—25')
    p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=20)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('钥匙串没有可用的Elsevier应用密钥')
    try:
        r = requests.get(URL, params={'query': query.strip(), 'start': start, 'count': count}, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('Elsevier网络请求失败：' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Elsevier接口返回 HTTP ' + str(r.status_code) + '，请核对查询及当前账户权限')
    try:
        d = r.json().get('search-results')
    except ValueError:
        raise RuntimeError('Elsevier返回非JSON') from None
    if not isinstance(d, dict) or not isinstance(d.get('entry', []), list):
        raise RuntimeError('Elsevier返回结构异常')
    items = [x for x in d.get('entry', []) if x.get('dc:identifier') or x.get('eid')]
    return {'source': 'Elsevier Scopus Search API', 'documentation': DOC, 'query': query.strip(), 'total': d.get('opensearch:totalResults'), 'start': d.get('opensearch:startIndex'), 'items_per_page': d.get('opensearch:itemsPerPage'), 'items': items, 'note': '官方API原始题录，保留引文及来源字段；无结果不代表数据库无该主题，引用数与订购范围会变化；实测跨请求结果顺序可能变动，分页可能重复或遗漏，应核对并避免假定穷尽。单次请求不自动限速或重试，非全文接口。'}

def detail_doi(doi):
    if not isinstance(doi, str) or len(doi) > 250 or (not re.fullmatch('10\\.\\d{4,9}/[^\\s?#]+', doi, re.I)):
        raise ValueError('请输入 DOI 本身，例如 10.1073/pnas.1213273110')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    try:
        r = requests.get('https://api.elsevier.com/content/abstract/doi/' + quote(doi, safe=''), params={'view': 'META_ABS'}, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Scopus 详情请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Scopus 详情返回 HTTP ' + str(r.status_code) + '；不能据此确定文章不存在或学校权限')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('Scopus 详情未返回 JSON') from None
    outer = d.get('abstracts-retrieval-response') if isinstance(d, dict) else None
    core = outer.get('coredata') if isinstance(outer, dict) else None
    if not isinstance(core, dict) or not isinstance(core.get('prism:doi'), str) or core['prism:doi'].casefold() != doi.casefold() or (not isinstance(core.get('dc:title'), str)):
        raise RuntimeError('Scopus 返回 DOI 或题名与请求不一致')
    fields = ('prism:doi', 'dc:identifier', 'eid', 'dc:title', 'dc:creator', 'dc:description', 'dc:publisher', 'prism:publicationName', 'prism:aggregationType', 'prism:coverDate', 'prism:issn', 'prism:volume', 'prism:issueIdentifier', 'prism:pageRange', 'prism:startingPage', 'prism:endingPage', 'subtype', 'subtypeDescription', 'citedby-count', 'openaccess', 'openaccessFlag', 'pubmed-id')
    return {'source': 'Elsevier Scopus Abstract Retrieval API（META_ABS）', 'documentation': 'https://dev.elsevier.com/documentation/AbstractRetrievalAPI.wadl', 'doi_requested': doi, 'coredata': {k: core[k] for k in fields if k in core}, 'affiliation_raw': outer.get('affiliation'), 'note': '仅返回官方摘要与原始元数据；引用数为查询时 Scopus 数据并会变化，字符串 0 不表示缺失。不是全文或学校逐篇订购证明；摘要可能缺失，需核对单项使用条件。'}

def author_search(query, start=0, count=5):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('作者查询表达式须为 1–250 字单行文本')
    if type(start) is not int or type(count) is not int or start < 0 or (not 1 <= count <= 25) or (start + count > 5000):
        raise ValueError('start 须为非负整数，count 为 1–25，且 start+count 不超过 5000')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    try:
        r = requests.get('https://api.elsevier.com/content/search/author', params={'query': query.strip(), 'start': start, 'count': count}, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Scopus 作者查询失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Scopus 作者查询返回 HTTP ' + str(r.status_code) + '；请检查查询和权限')
    try:
        d = r.json().get('search-results')
    except (ValueError, AttributeError):
        raise RuntimeError('Scopus 作者查询未返回预期 JSON') from None
    if not isinstance(d, dict) or not str(d.get('opensearch:totalResults', '')).isdigit() or (not str(d.get('opensearch:startIndex', '')).isdigit()) or (int(d['opensearch:startIndex']) != start) or (not isinstance(d.get('entry'), list)):
        raise RuntimeError('Scopus 作者查询总数、页码或结构异常')
    total = int(d['opensearch:totalResults'])
    entries = d['entry']
    if total == 0:
        if len(entries) > 1 or any((not isinstance(x, dict) or x.get('dc:identifier') or (not isinstance(x.get('error'), str)) for x in entries)):
            raise RuntimeError('Scopus 作者零结果与记录矛盾')
        entries = []
    if len(entries) > count:
        raise RuntimeError('Scopus 作者结果超过请求数量')
    items = []
    for x in entries:
        if not isinstance(x, dict) or not isinstance(x.get('dc:identifier'), str) or (not re.fullmatch('AUTHOR_ID:\\d+', x['dc:identifier'])) or (not isinstance(x.get('preferred-name'), dict)):
            raise RuntimeError('Scopus 作者记录缺少编号或姓名')
        items.append({k: x.get(k) for k in ('dc:identifier', 'eid', 'preferred-name', 'name-variant', 'document-count', 'subject-area', 'affiliation-current')})
    return {'source': 'Elsevier Scopus Author Search API', 'documentation': 'https://dev.elsevier.com/documentation/AuthorSearchAPI.wadl', 'query': query.strip(), 'start_requested': start, 'total_raw': d['opensearch:totalResults'], 'items': items, 'note': '姓名查询可能匹配变体和不同作者，需结合机构、领域及作者编号逐项消歧；作者档案及文献数会变化，最多查询前 5000 条，机构字段不等于当前任职证明。'}

def author_detail(author_id):
    if not isinstance(author_id, str) or not re.fullmatch('\\d{1,20}', author_id):
        raise ValueError('作者编号须为 1–20 位数字（不含 AUTHOR_ID: 前缀）')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    try:
        r = requests.get('https://api.elsevier.com/content/author/author_id/' + author_id, params={'view': 'STANDARD'}, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Scopus 作者详情请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Scopus 作者详情返回 HTTP ' + str(r.status_code) + '；不能据此判断作者是否存在或学校权限')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('Scopus 作者详情未返回 JSON') from None
    entries = d.get('author-retrieval-response') if isinstance(d, dict) else None
    if not isinstance(entries, list) or len(entries) != 1 or (not isinstance(entries[0], dict)):
        raise RuntimeError('Scopus 作者详情结构异常')
    e = entries[0]
    core = e.get('coredata')
    profile = e.get('author-profile')
    if not isinstance(core, dict) or core.get('dc:identifier') != 'AUTHOR_ID:' + author_id or (not isinstance(profile, dict)):
        raise RuntimeError('Scopus 作者编号或档案结构与请求不符')
    fields = ('dc:identifier', 'eid', 'document-count', 'citation-count', 'cited-by-count', 'h-index', 'orcid')
    pfields = ('preferred-name', 'name-variant', 'publication-range', 'affiliation-current', 'affiliation-history')
    return {'source': 'Elsevier Scopus Author Retrieval API（STANDARD）', 'documentation': 'https://dev.elsevier.com/documentation/AuthorRetrievalAPI.wadl', 'author_id_requested': author_id, 'coredata': {k: core[k] for k in fields if k in core}, 'profile': {k: profile[k] for k in pfields if k in profile}, 'subject_areas_raw': e.get('subject-areas'), 'note': '作者档案为 Scopus 的聚合结果，机构与署名仍需核对本人；文献数、引用次数、施引文献数等是不同指标并随时间变化，空值不视为零，不代表 JCR 指标或个人身份认证。'}

def affiliation_search(query, start=0, count=5):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 250 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('机构查询表达式须为 1–250 字单行文本')
    if type(start) is not int or type(count) is not int or start < 0 or (not 1 <= count <= 25) or (start + count > 5000):
        raise ValueError('start 须为非负整数，count 为 1–25，且 start+count 不超过 5000')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    try:
        r = requests.get('https://api.elsevier.com/content/search/affiliation', params={'query': query.strip(), 'start': start, 'count': count}, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Scopus 机构查询失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Scopus 机构查询返回 HTTP ' + str(r.status_code) + '；请检查查询和权限')
    try:
        d = r.json().get('search-results')
    except (ValueError, AttributeError):
        raise RuntimeError('Scopus 机构查询未返回预期 JSON') from None
    if not isinstance(d, dict) or not str(d.get('opensearch:totalResults', '')).isdigit() or (not str(d.get('opensearch:startIndex', '')).isdigit()) or (int(d['opensearch:startIndex']) != start) or (not isinstance(d.get('entry'), list)):
        raise RuntimeError('Scopus 机构查询总数、页码或结构异常')
    total = int(d['opensearch:totalResults'])
    entries = d['entry']
    if total == 0:
        if len(entries) > 1 or any((not isinstance(x, dict) or x.get('dc:identifier') or (not isinstance(x.get('error'), str)) for x in entries)):
            raise RuntimeError('Scopus 机构零结果与记录矛盾')
        entries = []
    if len(entries) > count:
        raise RuntimeError('Scopus 机构结果超过请求数量')
    fields = ('dc:identifier', 'eid', 'affiliation-name', 'name-variant', 'document-count', 'city', 'country', 'parent-affiliation-id')
    items = []
    for x in entries:
        if not isinstance(x, dict) or not isinstance(x.get('dc:identifier'), str) or (not re.fullmatch('AFFILIATION_ID:\\d+', x['dc:identifier'])) or (not isinstance(x.get('affiliation-name'), str)):
            raise RuntimeError('Scopus 机构记录缺少编号或名称')
        items.append({k: x.get(k) for k in fields})
    return {'source': 'Elsevier Scopus Affiliation Search API', 'documentation': 'https://dev.elsevier.com/documentation/AffiliationSearchAPI.wadl', 'query': query.strip(), 'start_requested': start, 'total_raw': d['opensearch:totalResults'], 'items': items, 'note': '机构名搜索可能包含相似名称、院系和其他学校，须结合机构 ID、城市及父机构逐条确认；机构和文献数会变化，最多查询前 5000 条。'}

def affiliation_detail(affiliation_id):
    if not isinstance(affiliation_id, str) or not re.fullmatch('\\d{1,20}', affiliation_id):
        raise ValueError('机构编号须为 1–20 位数字（不含 AFFILIATION_ID: 前缀）')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    try:
        r = requests.get('https://api.elsevier.com/content/affiliation/affiliation_id/' + affiliation_id, headers={'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError('Scopus 机构详情请求失败：' + type(exc).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('Scopus 机构详情返回 HTTP ' + str(r.status_code) + '；不能据此判断机构是否存在或学校权限')
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError('Scopus 机构详情未返回 JSON') from None
    e = d.get('affiliation-retrieval-response') if isinstance(d, dict) else None
    core = e.get('coredata') if isinstance(e, dict) else None
    if not isinstance(core, dict) or core.get('dc:identifier') != 'AFFILIATION_ID:' + affiliation_id or (not isinstance(e.get('affiliation-name'), str)):
        raise RuntimeError('Scopus 机构编号或名称与请求不符')
    fields = ('dc:identifier', 'eid', 'author-count', 'document-count')
    return {'source': 'Elsevier Scopus Affiliation Retrieval API', 'documentation': 'https://dev.elsevier.com/documentation/AffiliationRetrievalAPI.wadl', 'affiliation_id_requested': affiliation_id, 'affiliation_name_raw': e.get('affiliation-name'), 'name_variants_raw': e.get('name-variants'), 'city_raw': e.get('city'), 'country_raw': e.get('country'), 'institution_profile_raw': e.get('institution-profile'), 'coredata': {k: core[k] for k in fields if k in core}, 'note': '机构档案与计数为上游原值。2026-11-02 抽查浙大及浙大医学院：本详情接口文献数返回 0，但同一 ID 的机构检索返回非零，原因未知；不得将详情中的 0 直接解释为零篇，须另用机构检索及原站核对。机构档案不代表订购或全文权限。'}

def references_doi(doi, start=1, count=10):
    if not isinstance(doi, str) or len(doi) > 250 or (not re.fullmatch('10\\.\\d{4,9}/[^\\s?#]+', doi, re.I)):
        raise ValueError('请输入 DOI 本身')
    if type(start) is not int or type(count) is not int or (not 1 <= start <= 5000) or (not 1 <= count <= 40):
        raise ValueError('start 须为 1–5000 的整数，count 须为 1–40 的整数')
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', 'zju-research-toolkit', '-a', 'research-toolkit-elsevier', '-w'], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Elsevier 钥匙串密钥读取超时') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 Elsevier 应用密钥')
    u = 'https://api.elsevier.com/content/abstract/doi/' + quote(doi, safe='')
    h = {'X-ELS-APIKey': p.stdout.strip(), 'Accept': 'application/json'}

    def request(params):
        try:
            r = requests.get(u, params=params, headers=h, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError('Scopus 参考文献请求失败：' + type(exc).__name__) from None
        if r.status_code != 200:
            raise RuntimeError('Scopus 参考文献接口返回 HTTP ' + str(r.status_code) + '；越界或认证等原因需分别核对，不能当空结果')
        try:
            d = r.json()
        except ValueError:
            raise RuntimeError('Scopus 参考文献接口未返回 JSON') from None
        e = d.get('abstracts-retrieval-response') if isinstance(d, dict) else None
        if not isinstance(e, dict):
            raise RuntimeError('Scopus 参考文献响应结构异常')
        return e
    meta = request({'view': 'META'})
    core = meta.get('coredata')
    if not isinstance(core, dict) or not isinstance(core.get('prism:doi'), str) or core['prism:doi'].casefold() != doi.casefold() or (not isinstance(core.get('eid'), str)) or (not re.fullmatch('2-s2\\.0-\\d+', core['eid'])):
        raise RuntimeError('Scopus DOI 或 EID 无法核验')
    ref = request({'view': 'REF', 'startref': start, 'refcount': count}).get('references')
    if not isinstance(ref, dict) or not str(ref.get('@total-references', '')).isdigit() or (not isinstance(ref.get('link'), list)):
        raise RuntimeError('Scopus 参考文献总数或分页链接缺失')
    total = int(ref['@total-references'])
    raw = ref.get('reference', [])
    rows = [raw] if isinstance(raw, dict) else raw
    expected = min(count, max(0, total - start + 1))
    if not isinstance(rows, list) or len(rows) > expected or any((not isinstance(x, dict) for x in rows)):
        raise RuntimeError('Scopus 参考文献数量或结构异常')
    links = [x for x in ref['link'] if isinstance(x, dict) and x.get('@ref') == 'self']
    if len(links) != 1 or not isinstance(links[0].get('@href'), str):
        raise RuntimeError('Scopus 参考文献当前页链接缺失')
    link = urlsplit(links[0]['@href'])
    params = parse_qs(link.query)
    if link.scheme != 'https' or link.hostname != 'api.elsevier.com' or link.path != '/content/abstract/eid/' + core['eid'] or (params.get('view') != ['REF']) or (params.get('startref') != [str(start)]) or (params.get('refcount') != [str(count)]):
        raise RuntimeError('Scopus 参考文献返回文章或页码不一致')
    return {'source': 'Elsevier Scopus Abstract Retrieval API（REF）', 'documentation': 'https://dev.elsevier.com/documentation/AbstractRetrievalAPI.wadl', 'doi_requested': doi, 'eid_verified': core['eid'], 'start_requested': start, 'count_requested': count, 'total_raw': ref['@total-references'], 'returned_count': len(rows), 'page_complete_by_total': len(rows) == expected, 'items': rows, 'note': '先用 META 核对 DOI/EID，再核对 REF 的文章与分页链接；原始引文结构按站方保留。page_complete_by_total 仅比较本页条数与来源总数，不保证来源本身完整。start 从 1 开始，超过剩余条数时站方可能返回 400；单页不表示全部参考文献，引用覆盖与许可应以来源为准。'}
