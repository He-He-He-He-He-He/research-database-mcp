"""UNCTADstat code lists and dimension-filtered observations using OData schema."""
import release_runtime
import re, subprocess, xml.etree.ElementTree as ET
from unctadstat_datacentre_trade_adapter import _get, ROOT, PAGE
from unctadstat_general_economy_adapter import _report

def _schema(name, version):
    url = ROOT + '/datamart-api/' + name + '/' + str(version) + '/%24metadata'
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', '5000000', url], capture_output=True, timeout=35)
    if p.returncode or len(p.stdout) > 5000000:
        raise RuntimeError('UNCTAD OData schema 不可用')
    root = ET.fromstring(p.stdout)
    entitysets = {}
    fields = {}
    for x in root.iter():
        if x.tag.rsplit('}', 1)[-1] == 'EntitySet':
            entitysets[x.get('Name')] = x.get('EntityType', '').rsplit('.', 1)[-1]
        if x.tag.rsplit('}', 1)[-1] == 'EntityType' and x.get('Name') == 'Fact':
            for child in x:
                if child.tag.rsplit('}', 1)[-1] == 'Property' and child.get('Type', '').endswith('_DicItemRef'):
                    fields[child.get('Name')] = child.get('Type').rsplit('.', 1)[-1].removesuffix('_DicItemRef')
    mapping = {}
    for field, typ in fields.items():
        sets = [s for s, t in entitysets.items() if t == typ]
        if len(sets) == 1:
            mapping[field] = sets[0]
    return (url, mapping)

def structure(report):
    info, meta = _report(report)
    url, mapping = _schema(report, info['version'])
    return {'source': url, 'report': report, 'version': info['version'], 'fields_to_code_lists': mapping, 'report_metadata': meta, 'note': '由官方 schema 类型关联观测字段和代码表，不把代码出现视作任何国家、年份组合必有观测。'}

def codes(report, field, limit=50, offset=0):
    info, meta = _report(report)
    _, mapping = _schema(report, info['version'])
    if field not in mapping:
        raise ValueError('字段不在该报告可匹配代码表中')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('分页无效')
    url, result = _get('/datamart-api/' + report + '/' + str(info['version']) + '/' + mapping[field], {'$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'})
    if not isinstance(result, dict) or not isinstance(result.get('value'), list) or (not isinstance(result.get('@odata.count'), int)):
        raise ValueError('代码表响应异常')
    return {'source': url, 'report': report, 'version': info['version'], 'field': field, 'code_list': mapping[field], 'total': result['@odata.count'], 'offset': offset, 'rows': result['value'], 'note': '代码表可能包含地区汇总及父子层级，不能直接加总；代码出现不保证所选年份有值。'}

def facts(report, economy, year, filters=None, limit=20, offset=0):
    if not isinstance(economy, str) or not re.fullmatch('[0-9]{1,4}', economy):
        raise ValueError('经济体须为数字代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('年份无效')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('分页无效')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 8:
        raise ValueError('筛选条件须为最多 8 项 JSON 对象')
    info, meta = _report(report)
    _, mapping = _schema(report, info['version'])
    if 'Economy' not in mapping:
        raise ValueError('该表没有可核实的 Economy 字段，暂不支持')
    for k, v in filters.items():
        if k not in mapping or k == 'Economy' or (not isinstance(v, str)) or (not re.fullmatch('[A-Za-z0-9_.-]{1,80}', v)):
            raise ValueError('筛选字段或代码无效，请先查看 schema 与代码表')
    clause = [f'Year eq {year}', f"Economy/Code eq '{economy}'"] + [f"{k}/Code eq '{v}'" for k, v in filters.items()]
    url, result = _get('/datamart-api/' + report + '/' + str(info['version']) + '/Facts', {'$filter': ' and '.join(clause), '$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'})
    if not isinstance(result, dict) or not isinstance(result.get('value'), list) or (not isinstance(result.get('@odata.count'), int)):
        raise ValueError('观测响应异常')
    for row in result['value']:
        if row.get('Year') != year or row.get('Economy', {}).get('Code') != economy or any((str(row.get(k, {}).get('Code')) != v for k, v in filters.items())):
            raise ValueError('上游返回筛选范围外数据')
    return {'source': url, 'report': report, 'version': info['version'], 'report_metadata': meta, 'filters': filters, 'total': result['@odata.count'], 'offset': offset, 'rows': result['value'], 'note': '年度、经济体及所选分类匹配；保留完整字段、脚注、缺失与指标元数据。层级可能重叠；单位/倍率/来源及估计预测须查报告 Notes 和 measures。当前版本的历史数值可能已修订。'}
