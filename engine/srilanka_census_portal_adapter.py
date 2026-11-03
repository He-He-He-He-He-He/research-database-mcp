"""Sri Lanka DCS 2012/2024 census portal: indicator catalogue, areas, bounded observations."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://www.statistics.gov.lk/DashBoard/censusdataportal/'
LEVELS = {'province': ('provinces', 'p_table'), 'district': ('districts', 'd_table')}

def _session():
    s = requests.Session()
    s.trust_env = False
    return s

def _get(path):
    r = _session().get(BASE + path, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('响应超过大小上限')
    return r

def _categories():
    t = _get('alldatasqlite.php').text
    m = re.search('const\\s+categories\\s*=\\s*(\\[[^;]*\\]);', t)
    if not m:
        raise ValueError('官方指标目录结构发生变化')
    return json.loads(m.group(1))

def indicators(query='', limit=30):
    if not isinstance(query, str) or len(query) > 150 or (not 1 <= limit <= 100):
        raise ValueError('关键词或条数无效')
    rows = _categories()
    q = query.strip().casefold()
    matches = [v for v in rows if q in (str(v.get('label', '')) + ' ' + str(v.get('variable', '')) + ' ' + str(v.get('category', ''))).casefold()]
    return {'source': BASE + 'alldatasqlite.php', 'total': len(matches), 'items': matches[:limit], 'note': '标签与年份可用性来自官方门户；具体口径以普查报告为准。'}

def areas(year, level):
    if year not in (2012, 2024) or level not in LEVELS:
        raise ValueError('年份须为 2012 或 2024，地区层级须为 province 或 district')
    filename = str(year) + '-' + LEVELS[level][0] + '-topo.js'
    j = _get(filename).json()
    rows = []
    for obj in j['objects'].values():
        for g in obj.get('geometries', []):
            p = g.get('properties', {})
            rows.append({k: p.get(k) for k in ('ADM_ID', 'ADM_NAME', 'BELONGS_TO')})
    return {'source': BASE + filename, 'year': year, 'level': level, 'areas': rows}

def data(year, level, indicator, ids):
    if year not in (2012, 2024) or level not in LEVELS:
        raise ValueError('年份或地区层级无效')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,70}', indicator):
        raise ValueError('指标代码无效')
    if not isinstance(ids, list) or not 1 <= len(ids) <= 30 or any((not re.fullmatch('\\d{1,8}', str(x)) for x in ids)):
        raise ValueError('请提供 1–30 个数字地区代码')
    matches = [x for x in _categories() if x.get('variable') == indicator]
    if len(matches) != 1 or matches[0].get('is' + str(year)) != 'T':
        raise ValueError('指标不存在或官方目录未标明该年份可用')
    a = areas(year, level)
    amap = {str(v['ADM_ID']): v for v in a['areas']}
    ids = [str(x) for x in ids]
    if len(ids) != len(set(ids)) or any((x not in amap for x in ids)):
        raise ValueError('地区代码重复或不属于所选层级')
    payload = {'year': str(year), 'indicator': indicator, 'ids': ids, 'table': LEVELS[level][1] + '_' + str(year)}
    r = _session().post(BASE + 'fetch_data.php', json=payload, timeout=30)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('响应超过大小上限')
    values = r.json()
    if not isinstance(values, list) or any((not isinstance(x, dict) or str(x.get('ADM_ID')) not in ids or 'value' not in x for x in values)):
        raise ValueError('官方数据结构异常')
    return {'source': BASE + 'fetch_data.php', 'portal': BASE, 'year': year, 'level': level, 'indicator': matches[0], 'areas_source': a['source'], 'rows': [dict(amap[str(x['ADM_ID'])], value=x['value']) for x in values], 'note': '值保留官方原样；人口、百分比及其分母应以指标标签、目录和普查报告核对。门户未返回的地区并非零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('query', nargs='?', default='')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('areas')
    q.add_argument('year', type=int)
    q.add_argument('level', choices=LEVELS)
    q = s.add_parser('data')
    q.add_argument('year', type=int)
    q.add_argument('level', choices=LEVELS)
    q.add_argument('indicator')
    q.add_argument('ids', nargs='+')
    a = p.parse_args()
    out = indicators(a.query, a.limit) if a.cmd == 'indicators' else areas(a.year, a.level) if a.cmd == 'areas' else data(a.year, a.level, a.indicator, a.ids)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
