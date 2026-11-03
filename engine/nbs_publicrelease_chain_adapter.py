"""National Bureau of Statistics release-store annual indicator discovery and query."""
import release_runtime
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
ID = '[a-f0-9]{32}'

def _id(s):
    return isinstance(s, str) and re.fullmatch(ID, s)

def search(keyword, page=1, size=10, frequency='annual'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (type(page) is not int) or (not 1 <= page <= 1000) or (type(size) is not int) or (not 1 <= size <= 20):
        raise ValueError('invalid keyword or page')
    if frequency not in ('annual', 'quarterly', 'monthly'):
        raise ValueError('invalid frequency')
    response = get(BASE + '/query', {'search': keyword, 'pagenum': page, 'pageSize': size})
    d = response.get('data')
    if not response.get('success') or not isinstance(d, dict) or (not isinstance(d.get('data'), list)):
        raise RuntimeError('unexpected NBS search response')
    out = []
    for row in d['data']:
        if row.get('dt_type') != {'annual': 'YY', 'quarterly': 'SS', 'monthly': 'MM'}[frequency]:
            continue
        path = row.get('treeinfo_globalid', '').split('.')
        cid = row.get('cid')
        indicator = row.get('indic_id')
        if len(path) < 3 or any((not _id(x) for x in path)) or path[-1] != cid or (not _id(indicator)):
            raise RuntimeError('unrecognized catalog path; cannot infer root')
        out.append({'catalog_id': cid, 'indicator_id': indicator, 'root_id': path[1], 'name': row.get('show_name'), 'region_code': row.get('da'), 'region_name': row.get('da_name'), 'latest_period_label': row.get('dt_name'), 'sample_raw_value': row.get('value'), 'source_record': row})
    result = {'source': BASE + '/query', 'keyword': keyword, 'page': page, 'page_size': size, 'frequency': frequency, 'source_total_all_frequencies': d.get('count'), 'source_returned_rows': len(d['data']), 'candidates': out, 'note': '仅从当前搜索结果页挑选指定频率候选；上游搜索可能返回相近主题，须核对名称和单位。源返回条数可能与请求 pageSize 不同，跨页可能重复或变化；当前页无候选不代表其他页无结果。'}
    if frequency == 'annual':
        result['annual_candidates'] = out
    return result

def metadata(cid, indicator):
    if not _id(cid) or not _id(indicator):
        raise ValueError('invalid catalog or indicator ID')
    j = get(BASE + '/new/queryIndicatorsByCid', {'cid': cid})
    d = j.get('data')
    if not j.get('success') or not isinstance(d, dict) or (not isinstance(d.get('list'), list)):
        raise RuntimeError('unexpected NBS metadata response')
    matches = [x for x in d['list'] if x.get('_id') == indicator]
    if len(matches) != 1:
        raise ValueError('indicator absent or ambiguous in this catalog; check source search')
    return {'source': BASE + '/new/queryIndicatorsByCid', 'catalog_id': cid, 'indicator_id': indicator, 'indicator': matches[0], 'note': '指标定义、单位及注释以原始元数据为准；目录与地区的有效性需在查询中核对。'}

def annual(cid, indicator, root, start, end, region_code='000000000000', region_name='全国'):
    if not _id(root) or any((type(x) is not int for x in (start, end))) or (not 1900 <= start <= end <= 2100) or (end - start > 49):
        raise ValueError('invalid root or year range')
    if not isinstance(region_code, str) or not re.fullmatch('[0-9]{12}', region_code) or (not isinstance(region_name, str)) or (not region_name) or (len(region_name) > 50):
        raise ValueError('invalid region')
    meta = metadata(cid, indicator)
    body = {'cid': cid, 'indicatorIds': [indicator], 'das': [{'text': region_name, 'value': region_code}], 'dts': [f'{start}YY-{end}YY'], 'showType': '1', 'rootId': root}
    j = get(BASE + '/stream/esData', body=body)
    rows = j.get('data')
    if not j.get('success') or not isinstance(rows, list):
        raise RuntimeError('unexpected NBS data response')
    for row in rows:
        code = row.get('code', '')
        if not re.fullmatch('\\d{4}YY', code) or not start <= int(code[:4]) <= end or (not isinstance(row.get('values'), list)):
            raise RuntimeError('response contains unexpected period')
        if any((v.get('_id') != indicator or v.get('da') != region_code for v in row['values'])):
            raise RuntimeError('response contains unexpected indicator or region')
    return {'source': BASE + '/stream/esData', 'request': body, 'metadata': meta['indicator'], 'data': rows, 'note': '年度序列保留源字段、单位、空值和期间；空值不等于零。搜索结果的地区与指标必须核对，地区代码与名称需来自官方目录；源数据可修订。'}

def series(cid, indicator, root, frequency, start, end, region_code='000000000000', region_name='全国'):
    if frequency not in ('annual', 'quarterly', 'monthly'):
        raise ValueError('invalid frequency')

    def period(v):
        if not isinstance(v, str):
            raise ValueError('period must be a string')
        if frequency == 'annual' and re.fullmatch('(19|20)\\d{2}', v):
            return ((int(v), 0), v + 'YY')
        if frequency == 'quarterly' and re.fullmatch('(19|20)\\d{2}Q[1-4]', v):
            return ((int(v[:4]), int(v[-1])), v[:4] + '0' + v[-1] + 'SS')
        if frequency == 'monthly' and re.fullmatch('(19|20)\\d{2}-(0[1-9]|1[0-2])', v):
            return ((int(v[:4]), int(v[-2:])), v.replace('-', '') + 'MM')
        raise ValueError('period format: annual YYYY, quarterly YYYYQ1, monthly YYYY-MM')
    a, sa = period(start)
    b, sb = period(end)
    if a > b or b[0] - a[0] > 49 or (not _id(root)):
        raise ValueError('invalid period range or root')
    if not isinstance(region_code, str) or not re.fullmatch('[0-9]{12}', region_code) or (not isinstance(region_name, str)) or (not region_name) or (len(region_name) > 50):
        raise ValueError('invalid region')
    from nbs_new_national_timeseries_adapter import categories
    roots = categories(frequency)
    if len(roots) != 1 or roots[0].get('_id') != root:
        raise ValueError('root does not match selected frequency')
    meta = metadata(cid, indicator)
    body = {'cid': cid, 'indicatorIds': [indicator], 'das': [{'text': region_name, 'value': region_code}], 'dts': [sa + '-' + sb], 'showType': '1', 'rootId': root}
    j = get(BASE + '/stream/esData', body=body)
    rows = j.get('data')
    if not j.get('success') or not isinstance(rows, list):
        raise RuntimeError('unexpected NBS response')
    for row in rows:
        code = row.get('code', '')
        if frequency == 'annual':
            m = re.fullmatch('(\\d{4})YY', code)
        elif frequency == 'quarterly':
            m = re.fullmatch('(\\d{4})0([1-4])SS', code)
        else:
            m = re.fullmatch('(\\d{4})(0[1-9]|1[0-2])MM', code)
        if not m or not a <= ((int(m.group(1)), int(m.group(2))) if frequency != 'annual' else (int(m.group(1)), 0)) <= b or (not isinstance(row.get('values'), list)):
            raise RuntimeError('response contains unexpected period')
        if any((v.get('_id') != indicator or v.get('da') != region_code for v in row['values'])):
            raise RuntimeError('response contains unexpected indicator or region')
    return {'source': BASE + '/stream/esData', 'request': body, 'frequency': frequency, 'metadata': meta['indicator'], 'data': rows, 'note': '保留原始单位、空值及统计口径；季度和月度数据可能为累计量，不应推成单期值。根目录已核对频率，地区名称代码仍需核对；源可修订。'}
