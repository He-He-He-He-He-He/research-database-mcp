"""国家知识产权局 2025 商标统计年报公开表。"""
import release_runtime
import subprocess
from moe_education_statistics_adapters import _LeafTables
ROOT = 'https://www.cnipa.gov.cn/tjxx/jianbao/year2025/g/'
CATALOG = {'g1': '分国内外商标申请注册年度状况', 'g2': '分地区国内商标申请、注册及有效注册量'}

def trademark_tables(keyword=''):
    return [{'code': k, 'title': v, 'url': ROOT + k + '.html'} for k, v in CATALOG.items() if keyword in v]

def trademark_table(code):
    if code not in CATALOG:
        raise ValueError('仅支持已实测的 g1 和 g2 表')
    url = ROOT + code + '.html'
    args = ['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url]
    html = release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8')
    p = _LeafTables()
    p.feed(html)
    tables = [t for t in p.tables if len(t) >= 3]
    if not tables:
        raise ValueError('未读取到统计表，上游结构可能变化')
    return {'code': code, 'title': CATALOG[code], 'url': url, 'tables': tables, 'note': '单位件，申请量、注册量为期间量，有效注册量为期末存量；按原表表头及注释解释。'}
