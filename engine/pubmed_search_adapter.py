"""PubMed ESearch IDs with explicitly bounded pagination."""
import release_runtime
import re
import requests
URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
DOC = 'https://www.ncbi.nlm.nih.gov/books/NBK25499/'

def search(query, size=5, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('检索式须为 1–1000 个非控制字符')
    if type(size) is not int or not 1 <= size <= 9999 or type(offset) is not int or (offset < 0) or (offset + size > 9999):
        raise ValueError('size 须为 1–9999，offset 非负且 offset + size 不得超过 9999')
    params = {'db': 'pubmed', 'term': query.strip(), 'retmode': 'json', 'retmax': size, 'retstart': offset, 'tool': 'personal_research_cli'}
    try:
        response = requests.get(URL, params=params, timeout=25)
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError('PubMed 请求失败或返回非 JSON') from None
    result = body.get('esearchresult') if isinstance(body, dict) else None
    if not isinstance(result, dict) or not isinstance(result.get('idlist'), list):
        raise RuntimeError('PubMed 检索响应结构异常')
    try:
        count = int(result['count'])
        actual = int(result['retstart'])
        returned = int(result['retmax'])
    except (KeyError, ValueError, TypeError):
        raise RuntimeError('PubMed 分页信息异常') from None
    ids = result['idlist']
    if count < 0 or actual != offset or returned != len(ids) or (len(ids) > size) or any((not isinstance(x, str) or not x.isascii() or (not x.isdigit()) for x in ids)):
        raise RuntimeError('PubMed 返回页码、数量或标识不符')
    return {**body, 'toolkit_documentation': DOC, 'toolkit_note': 'NCBI 文档称 PubMed ESearch 可取前 10000 条；当前源端实测边界为前 9999 条，故本工具保守限制 offset + size 不超过 9999；更深结果需按日期等条件拆分或使用 NCBI EDirect。结果会随索引更新而变化，跨请求分页可能重叠或遗漏。此接口仅返回 PubMed 编号，题录需用 pubmed-summary 获取。'}
