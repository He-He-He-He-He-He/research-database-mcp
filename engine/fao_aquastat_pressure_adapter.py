"""Read the specific public AQUASTAT pressure-on-water-resources view observed in its UI."""
import release_runtime
import csv, io, subprocess
from urllib.parse import urlencode
PAGE = 'https://data.apps.fao.org/aquastat/'
API = 'https://api.data.apps.fao.org/api/v2/bigquery'
SQL = 'https://data.apps.fao.org/catalog/dataset/945666e6-7803-4621-b8ef-cfd885a84596/resource/4a000a1b-24f0-4328-aab6-b9b525892090/download/query_en.sql'
PARAMS = {'sql_url': SQL, 'area': 'World', 'type': 'all', 'variable': '4016', 'year': '2023,2022,2021'}
FIELDS = {'Country', 'Variable', 'Year', 'Value', 'Unit', 'Symbol', 'SymbolDescription', 'm49', 'VariableCode', 'SubgroupCode'}

def query(country='', variable='', year='', offset=0, limit=20):
    if any((len(v) > 100 for v in (country, variable, year))) or (year and year not in ('2021', '2022', '2023')):
        raise ValueError('筛选值不合法；年份仅支持 2021、2022、2023')
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError('offset 须非负，limit 须为 1 至 100')
    url = API + '?' + urlencode(PARAMS)
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '60', '--max-filesize', '10000000', url], capture_output=True, timeout=65)
    if p.returncode:
        raise RuntimeError('FAO AQUASTAT 请求失败：' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 10000000:
        raise RuntimeError('返回数据超出大小限制')
    reader = csv.DictReader(io.StringIO(p.stdout.decode('utf-8-sig')))
    if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
        raise RuntimeError('FAO 返回格式发生变化')
    items = []
    n = 0
    total = 0
    for row in reader:
        total += 1
        if row['SubgroupCode'] != '4016' or row['Year'] not in ('2021', '2022', '2023'):
            raise RuntimeError('上游返回范围与已核验视图不一致')
        if country and country.casefold() not in (row['Country'].casefold(), row['m49']):
            continue
        if variable and variable.casefold() not in (row['VariableCode'].casefold(), row['Variable'].casefold()):
            continue
        if year and row['Year'] != year:
            continue
        if offset <= n < offset + limit:
            items.append(row)
        n += 1
    return {'source': 'FAO AQUASTAT', 'source_page': PAGE, 'query_url': url, 'view': 'Pressure on water resources; World; all types; 2021–2023', 'source_rows': total, 'matched_rows': n, 'offset': offset, 'items': items, 'note': '国家名或联合国 M49 代码、指标英文全称或代码及年份在本地精确筛选；返回原始字符串、单位、数据标记及其解释。视图数据可能事后修订；不代表某历史日期已发布。World 为界面选择的地区范围，并非全球合计。'}
