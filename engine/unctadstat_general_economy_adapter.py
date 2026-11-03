"""UNCTADstat report metadata and generic annual economy-level facts."""
import release_runtime
import re
from unctadstat_datacentre_trade_adapter import _get, _reports, ROOT, PAGE

def _report(name):
    if not isinstance(name, str) or not re.fullmatch('[A-Za-z0-9_.]{1,100}', name):
        raise ValueError('无效报告标识')
    matches = [r for r in _reports() if r.get('name') == name]
    if len(matches) != 1 or not isinstance(matches[0].get('version'), int):
        raise ValueError('目录中未找到唯一当前版本')
    info = matches[0]
    _, meta = _get('/api/datacenter/reports/' + name + '/info/' + str(info['version']))
    if not isinstance(meta, dict) or meta.get('name') != name:
        raise ValueError('上游报告元数据不匹配')
    return (info, meta)

def details(name):
    info, meta = _report(name)
    return {'source': ROOT + '/api/datacenter/reports/' + name + '/info/' + str(info['version']), 'page': PAGE, 'catalog_entry': info, 'report_metadata': meta, 'note': '当前报告版本及方法、指标和维度；旧年份数据可能经修订，原始来源及估计方法以表内 Notes 为准。'}

def facts(name, economy, year, limit=20, offset=0):
    if not isinstance(economy, str) or not re.fullmatch('[0-9]{1,4}', economy):
        raise ValueError('经济体须使用 UNCTAD 数字代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('年份超限')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 100000):
        raise ValueError('分页超限')
    info, meta = _report(name)
    dims = {d.get('name') for d in meta.get('dims', []) if isinstance(d, dict)}
    if not {'Years', 'Economies'}.issubset(dims):
        raise ValueError('此报告元数据不含年度及经济体维度，当前查询方式暂不支持')
    ver = info['version']
    params = {'$filter': f"Year eq {year} and Economy/Code eq '{economy}'", '$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'}
    url, result = _get('/datamart-api/' + name + '/' + str(ver) + '/Facts', params)
    if not isinstance(result, dict) or not isinstance(result.get('value'), list) or (not isinstance(result.get('@odata.count'), int)):
        raise ValueError('上游数据结构异常')
    for row in result['value']:
        if row.get('Year') != year or row.get('Economy', {}).get('Code') != economy:
            raise ValueError('上游返回了筛选范围之外的数据')
    return {'source': url, 'page': PAGE, 'report': name, 'version': ver, 'catalog_entry': info, 'report_metadata': meta, 'total': result['@odata.count'], 'offset': offset, 'rows': result['value'], 'note': '仅支持有年度和经济体维度的报告；其他分类/层级可能重叠，分页总数不是独立统计量。保留原始字段、计量代码、脚注及缺失；逐表 measures 与 Notes 核对单位、来源、地区与估计/预测。当前版本可能修订历史值，不能仅凭数据年份认定历史已发布。'}
