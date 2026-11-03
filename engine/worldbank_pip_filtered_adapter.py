"""World Bank PIP versions and parameterised poverty/inequality observations."""
import release_runtime
import re, math
import worldbank_pip_adapter as api

def versions(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('版本关键词无效')
    rows = api._get('versions', {})
    if not isinstance(rows, list) or any((not isinstance(x, dict) or not isinstance(x.get('version'), str) for x in rows)):
        raise RuntimeError('版本目录结构异常')
    found = [x for x in rows if keyword.casefold() in str(x.get('version', '')).casefold()]
    return {'source_url': api.BASE + 'versions', 'keyword': keyword, 'matched': len(found), 'items': found, 'note': '这是当前 API 公布的版本目录；列出不保证历史版本仍能成功取数，版本代码中的日期不独立证明当时已公开或文件未修订。PPP 基期与返回记录中的 ppp 转换因子不同。'}

def data(country, year='all', version='', poverty_line=None, reporting_level='all', welfare_type='all', fill_gaps=False):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家须为三个大写字母')
    if year != 'all' and (type(year) is not int or not 1900 <= year <= 2100):
        raise ValueError('年份须为 all 或有效年份')
    if reporting_level not in ('all', 'national', 'rural', 'urban') or welfare_type not in ('all', 'income', 'consumption') or type(fill_gaps) is not bool:
        raise ValueError('口径或插值参数无效')
    if not isinstance(version, str) or len(version) > 100:
        raise ValueError('版本无效')
    if poverty_line is not None and (isinstance(poverty_line, bool) or not isinstance(poverty_line, (int, float)) or (not math.isfinite(poverty_line)) or (poverty_line <= 0)):
        raise ValueError('贫困线须为正数')
    chosen = None
    if version:
        rows = versions()['items']
        hits = [r for r in rows if r['version'] == version]
        if len(hits) != 1:
            raise ValueError('版本不在当前官方版本目录')
        chosen = hits[0]
    p = {'country': country, 'year': year, 'format': 'json', 'reporting_level': reporting_level, 'welfare_type': welfare_type, 'fill_gaps': str(fill_gaps).lower()}
    if version:
        p['version'] = version
    if poverty_line is not None:
        p['povline'] = poverty_line
    rows = api._get('pip', p)
    if not isinstance(rows, list) or any((not isinstance(r, dict) for r in rows)):
        raise RuntimeError('PIP 数据响应异常')
    for r in rows:
        if r.get('country_code') != country or (year != 'all' and r.get('reporting_year') != year):
            raise RuntimeError('返回国家或年份不符')
        if reporting_level != 'all' and r.get('reporting_level') != reporting_level:
            raise RuntimeError('返回城乡口径不符')
        if welfare_type != 'all' and r.get('welfare_type') != welfare_type:
            raise RuntimeError('返回福利指标类型不符')
    return {'source_url': api.BASE + 'pip', 'request': p, 'requested_version_metadata': chosen, 'count': len(rows), 'rows': rows, 'note': 'headcount 为比例，非百分数；贫困线单位为所选版本 PPP 国际元/人/日，ppp 字段为换算因子而非基期。收入与消费、城乡、调查年份与报告年份不可混用；fill_gaps 可产生插补，查看 is_interpolated、estimate_type 和调查年份。版本是请求值，上游单行未回显版本；旧版本可能失败，不能按版本字符串推定历史发布日期。'}
