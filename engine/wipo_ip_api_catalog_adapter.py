"""Read paginated WIPO API catalog entries, not the listed third-party APIs."""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
ENDPOINT = 'https://apicatalog.wipo.int/api/apis'
INFO = 'https://www.wipo.int/en/web/standards/ip-api-catalog/index'
USER_GUIDE = 'https://www.wipo.int/en/web/standards/ip-api-catalog/user-guide'
TERMS = 'https://www.wipo.int/en/web/terms-of-use'
DOMAINS = ('PATENT', 'TRADEMARK', 'INDUSTRIAL_DESIGN', 'COPYRIGHT', 'GEOGRAPHICAL_INDICATION', 'PLANT_VARIETY_PROTECTION', '8c5b0dce')

def search(keyword='', domain='', offset=0, limit=10):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词应为至多100个可打印字符')
    if domain and domain not in DOMAINS:
        raise ValueError('未知知识产权领域')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 20):
        raise ValueError('偏移须为0—10000，条数须为1—20')
    params = {'start': offset, 'size': limit}
    if keyword.strip():
        params['searchParameter'] = keyword.strip()
    if domain:
        params['ipDomainValues'] = domain
    url = ENDPOINT + '?' + urlencode(params)
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '2000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('WIPO 请求失败: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 2000000:
        raise RuntimeError('响应超限')
    d = json.loads(p.stdout)
    if not isinstance(d, dict) or d.get('start') != offset or (not isinstance(d.get('size'), int)) or (not isinstance(d.get('totalCount'), int)) or (not isinstance(d.get('results'), list)) or (d['size'] != len(d['results'])) or (d['size'] > limit):
        raise RuntimeError('WIPO 返回格式或分页异常')
    results = []
    for x in d['results']:
        cats = x.get('searchCatalogues', [])
        if not isinstance(cats, list):
            raise RuntimeError('分类格式异常')
        classification = {i['key']: i.get('indexValues', []) for i in cats if isinstance(i, dict) and isinstance(i.get('key'), str)}
        if domain and domain not in classification.get('IPDOMAIN', []):
            raise RuntimeError('返回领域与筛选条件不一致')
        results.append({'id': x.get('idAPI'), 'title': x.get('title'), 'description': x.get('description'), 'institution_code': x.get('organization'), 'website': x.get('specWebsite'), 'protocol_type': x.get('type'), 'website_alive_flag': x.get('alive'), 'updated_at': x.get('updatedAt'), 'classifications': classification})
    return {'source': 'WIPO API Catalog for Intellectual Property', 'source_page': INFO, 'catalog_url': url, 'user_guide': USER_GUIDE, 'terms': TERMS, 'keyword': keyword.strip(), 'domain': domain, 'offset': offset, 'limit': limit, 'total_reported': d['totalCount'], 'items': results, 'note': 'WIPO 目录网页当前使用的公开分页响应，不是被列举的第三方专利数据库或 API 本身；目录可能不完整、滞后或含支付/账户等非只读接口，实际可用性、费用、访问权限及 AI 许可须向对应机构逐项核实。网站状态标记不保证现在可用。'}
