"""NOAA LSA 全球卫星海平面距平，按源文件保留各卫星观测。"""
import release_runtime
import argparse, csv, io, json, subprocess
URL = 'https://star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/slr/slr_sla_gbl_keep_ref_90.csv'
SATELLITES = ('TOPEX/Poseidon', 'Jason-1', 'Jason-2', 'Jason-3', 'Sentinel-6MF')

def global_sea_level(start=1992, end=2100, limit=100):
    if isinstance(start, bool) or isinstance(end, bool) or (not isinstance(start, int)) or (not isinstance(end, int)) or (not 1900 <= start <= end <= 2100) or (not 1 <= int(limit) <= 10000):
        raise ValueError('年份范围或记录数量无效')
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', URL], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('NOAA 数据请求失败: ' + p.stderr.strip())
    lines = p.stdout.splitlines()
    comments = [x for x in lines if x.startswith('#')]
    reader = csv.DictReader(io.StringIO('\n'.join((x for x in lines if not x.startswith('#')))))
    if not reader.fieldnames or not set(('year',) + SATELLITES).issubset(reader.fieldnames):
        raise RuntimeError('NOAA 格式变更')
    out = []
    all_years = []
    for row in reader:
        y = float(row['year'])
        all_years.append(y)
        if start <= y < end + 1:
            vals = {s: float(row[s]) for s in SATELLITES if row.get(s)}
            if vals:
                out.append({'decimal_year': y, 'sea_level_anomaly_mm': vals, 'raw_row': row})
    if not all_years:
        raise RuntimeError('NOAA 返回空序列')
    return {'source': 'NOAA Laboratory for Satellite Altimetry', 'source_url': URL, 'metadata_url': 'https://star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/LSA_SLR_timeseries_global.php', 'unit': 'mm', 'scope': '卫星测高全球平均海平面距平（66°S–66°N），保留季节信号；应用反气压修正，未作冰川均衡调整；不同卫星原始列未拼接。NOAA 标注为实验用途，非正式业务产品。文件可能滞后，参见 source_latest_decimal_year；截断时返回源文件末尾记录，可缩小年份范围。raw_row 保留原始列和缺失标记。', 'acknowledgment': 'Altimetry data are provided by NOAA Laboratory for Satellite Altimetry.', 'source_first_decimal_year': min(all_years), 'source_latest_decimal_year': max(all_years), 'source_comments': comments, 'matching_rows': len(out), 'returned_rows': min(len(out), int(limit)), 'truncated': len(out) > int(limit), 'items': out[-int(limit):]}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=int, default=1992)
    p.add_argument('--end', type=int, default=2100)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(global_sea_level(a.start, a.end, a.limit), ensure_ascii=False, indent=2))
