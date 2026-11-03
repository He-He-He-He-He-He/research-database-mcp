"""NOAA GML 全球海洋表面氧化亚氮干空气摩尔分数月均值。"""
import release_runtime
import argparse, csv, io, json, re, subprocess
URL = 'https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv'

def nitrous_oxide_monthly(start='2001-01', end=None, limit=36):
    for x in (start, end):
        if x is not None and (not isinstance(x, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', x)):
            raise ValueError('月份须为 YYYY-MM')
    if start and end and (start > end):
        raise ValueError('开始月份不能晚于结束月份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 应为 1–1000')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', URL], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('NOAA 请求失败: ' + p.stderr.strip())
    reader = csv.DictReader(io.StringIO('\n'.join((x for x in p.stdout.splitlines() if x and (not x.startswith('#'))))))
    if not reader.fieldnames or not {'year', 'month', 'decimal', 'average', 'average_unc', 'trend', 'trend_unc'}.issubset(reader.fieldnames):
        raise RuntimeError('NOAA 数据结构异常')
    out = []
    for r in reader:
        period = f"{int(r['year']):04d}-{int(r['month']):02d}"
        if start and period < start or (end and period > end):
            continue

        def val(k):
            v = float(r[k])
            return None if v < 0 else v
        out.append({'period': period, 'average_ppb': val('average'), 'average_uncertainty_ppb': val('average_unc'), 'trend_ppb': val('trend'), 'trend_uncertainty_ppb': val('trend_unc'), 'raw_values': {k: r[k] for k in ('decimal', 'average', 'average_unc', 'trend', 'trend_unc')}})
    out.sort(key=lambda x: x['period'], reverse=True)
    return {'source': 'NOAA Global Monitoring Laboratory', 'source_url': URL, 'documentation': 'https://gml.noaa.gov/ccgg/trends_n2o/', 'doi': 'https://doi.org/10.15138/P8XG-AA10', 'scope': '结果按月份倒序；truncated 为 true 时可提高 limit（最多1000）或缩小月份范围。全球海洋表面站点月均大气氧化亚氮干空气摩尔分数（ppb，nmol/mol），非排放量；trend 是去季节趋势；源数据 -9.99 缺失值转换为 null。近期及历史数据可能修订。', 'start': start, 'end': end, 'total_matching': len(out), 'limit': limit, 'truncated': len(out) > limit, 'items': out[:limit]}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--start', default='2001-01')
    p.add_argument('--end')
    p.add_argument('--limit', type=int, default=36)
    a = p.parse_args()
    print(json.dumps(nitrous_oxide_monthly(a.start, a.end, a.limit), ensure_ascii=False, indent=2))
