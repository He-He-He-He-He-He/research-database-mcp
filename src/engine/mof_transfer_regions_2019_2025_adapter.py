"""Central-to-local transfers by region, MOF final accounts 2019–25."""
import release_runtime
import mof_final_accounts_2016_2019_adapter as a
import mof_final_accounts_2020_2023_adapter as b
import mof_national_final_accounts_2024_2025_adapter as c
KINDS = {'general': '中央对地方转移支付分地区决算表', 'fund': '中央对地方政府性基金转移支付分地区决算表'}

def search(year, kind='general', region=''):
    if type(year) is not int or not 2019 <= year <= 2025:
        raise ValueError('year must be 2019–2025')
    if kind not in KINDS:
        raise ValueError('kind must be general or fund')
    if not isinstance(region, str) or len(region) > 100:
        raise ValueError('invalid region')
    if year == 2019 and kind == 'fund':
        raise ValueError('2019 fund regional table not found in official catalog')
    adapter = a if year == 2019 else b if year <= 2023 else c
    entries = adapter.catalog(year, KINDS[kind])['items']
    if len(entries) != 1:
        raise ValueError('expected unique regional table')
    r = adapter.table(year, entries[0]['url'])
    if len(r['tables']) != 1:
        raise ValueError('expected one data table')
    rows = r['tables'][0]
    q = ''.join(region.split())
    matched = [{'row': i, 'cells': row} for i, row in enumerate(rows, 1) if q in ''.join((''.join(cell['text'].split()) for cell in row))]
    return {'year': year, 'kind': kind, 'title': entries[0]['title'], 'url': entries[0]['url'], 'headers': rows[:3], 'rows': matched, 'matched_rows': len(matched), 'source': '财政部中央对地方分地区转移支付决算表', 'note': '保留原始预算、决算列与合并单元格；地区名可能同时匹配含及不含计划单列市行，勿将其相加。一般公共预算和政府性基金口径不同；不同年份列数、预算及决算口径按原表头。'}
