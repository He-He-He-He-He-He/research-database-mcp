"""One-page faceted title search for China epigraphic trial catalogue."""
import release_runtime
import html
import re
import requests
URL = 'http://121.89.86.151:8000/api/v1/search/'

def search(keyword, dynasty='', author='', font='', page=1, timeout=25, field='name'):
    if field not in ('name', 'author', 'collector', 'dynasty', 'font', 'all', 'alias', 'era_name', 'language', 'inscription', 'main_inscription', 'material', 'form', 'shape', 'composition', 'inscriber', 'excavation_site', 'source', 'detail_content'):
        raise ValueError('unsupported search field')
    for label, value in [('keyword', keyword), ('dynasty', dynasty), ('author', author), ('font', font)]:
        if not isinstance(value, str) or len(value) > 100 or (label == 'keyword' and (not value.strip())):
            raise ValueError(f'{label} must be a string of at most 100 characters')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be between 1 and 100')
    facet = {'cates_id': '', 'authors': author, 'dynasties': dynasty, 'commonEra': '', 'fonts': font}
    payload = {'item_group': [], 'search_option': field, 'search_cate_option_id': 7, 'search_text': keyword.strip(), 'search_term': 'match', 'facet': facet, 'page': page, 'pageSize': 20}
    r = requests.post(URL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json().get('datas')
    if not isinstance(data, dict) or not isinstance(data.get('list_datas'), list) or 'size' not in data:
        raise ValueError('unexpected search response')
    if type(data['size']) is not int or data['size'] < 0:
        raise ValueError('unexpected search total')
    expected = min(20, max(0, data['size'] - (page - 1) * 20))
    if len(data['list_datas']) != expected:
        raise ValueError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')

    def clean(value):
        return html.unescape(re.sub('<[^>]*>', '', value)) if isinstance(value, str) else value
    fields = ('id', 'info_id', 'name', 'alias', 'dynasty', 'author', 'font', 'material', 'chronology', 'excavation_site')
    extra = field if field not in fields and field not in ('all', 'detail_content') else None
    facets = {}
    for key in ('dynasty_datas', 'author_datas', 'fonts_datas'):
        facets[key] = [{'name': x.get('name'), 'count': x.get('doc_count')} for x in data.get(key, []) if isinstance(x, dict)]
    records = [{k: clean(x.get(k)) for k in fields} for x in data['list_datas']]
    for item, row in zip(records, data['list_datas']):
        raw = row.get('name')
        if raw is not None and (not isinstance(raw, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', raw, re.I)):
            item['name_raw'] = None
            item['name_raw_omitted'] = True
            cleaned = item['name']
            if cleaned is not None and (not isinstance(cleaned, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:token|session|sid|apikey|api_key)\\s*=', cleaned, re.I)):
                item['name'] = None
        else:
            item['name_raw'] = raw
    if extra:
        for item, row in zip(records, data['list_datas']):
            value = clean(row.get(extra))
            if isinstance(value, str) and (re.search('https?://|[?&](?:token|session|key)=', value, re.I) or len(value) > 10000):
                item['field_suppressed'] = True
            else:
                item[extra] = value
    result = {'source': '中国金石总录试用库', 'keyword': keyword.strip(), 'page': page, 'filters': {'dynasty': dynasty, 'author': author, 'font': font}, 'total': data['size'], 'records': records, 'facets': facets, 'note': '馆方列试用至 2026-12-31；机构身份、自动读取、全文及图像权限未确认。上游 HTTP，勿发送敏感词；按总数和请求页次校验固定源页条数，源未回显页码，数据可能变化。安全 name_raw 保留高亮，含链接或疑似凭据则省略标记。'}
    if field != 'name':
        result['field_requested'] = field
        result['note'] += ' 站方未回显请求字段及页码；结果可能匹配繁简异体，请核对原始字段。'
        if field in ('all', 'detail_content'):
            result['note'] += ' 仅返回题录，不返回录文全文。'
    return result
