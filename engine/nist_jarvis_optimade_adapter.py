"""Bounded exact formula query to NIST JARVIS-DFT OPTIMADE public API."""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
ENDPOINT = 'https://jarvis.nist.gov/optimade/jarvisdft/v1/structures/'
INFO = 'https://jarvis.nist.gov/optimade/jarvisdft/'
TERMS = 'https://www.nist.gov/copyrights-disclaimers'

def search(formula, page=1, limit=20):
    if not isinstance(formula, str) or not re.fullmatch('[A-Z][A-Za-z0-9]{0,39}', formula):
        raise ValueError('化学式只能包含字母与数字，且以大写字母开头')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 20):
        raise ValueError('页码须1—100，输出条数须1—20')
    url = ENDPOINT + '?' + urlencode({'filter': 'chemical_formula_reduced="' + formula + '"', 'page': page})
    p = release_runtime.run(['/usr/bin/curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '35', '--max-filesize', '8000000', url], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('NIST 请求失败: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8000000:
        raise RuntimeError('NIST 响应超过8MB')
    d = json.loads(p.stdout)
    data = d.get('data')
    meta = d.get('meta')
    links = d.get('links')
    if not isinstance(data, list) or not isinstance(meta, dict) or (not isinstance(links, dict)) or (meta.get('provider', {}).get('name') != 'NIST-JARVIS'):
        raise RuntimeError('NIST 返回结构异常')
    if any((not isinstance(x, dict) or x.get('attributes', {}).get('chemical_formula_reduced') != formula for x in data)):
        raise RuntimeError('上游返回化学式与请求不一致')
    return {'source': 'NIST JARVIS-DFT OPTIMADE', 'source_page': INFO, 'source_url': url, 'terms': TERMS, 'formula': formula, 'page': page, 'upstream_page_size_actual': len(data), 'upstream_data_returned_field': meta.get('data_returned'), 'upstream_more_data_available': meta.get('more_data_available'), 'upstream_next': links.get('next'), 'returned_count': min(limit, len(data)), 'client_truncated': len(data) > limit, 'items': data[:limit], 'note': 'DFT计算材料结构及属性，不等同实验测量、工业材料牌号或 Total Materia。保留官方原始属性与数值，具体方法、单位和适用性须查数据说明；目前观察到上游 page_limit 不生效，data_returned 有时不同于本页条数，nelements/elements 也可能与通常的不同元素数量含义不一致，均不推断。这里只按请求页获取后本地截取，非全结果；若client_truncated为true，翻下一源页会遗漏当前页余项，请使用limit=20读取本次观测到的完整源页。'}
