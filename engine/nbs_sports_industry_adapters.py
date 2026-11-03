"""国家统计局全国体育产业总产出与增加值。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
URLS = {2022: 'https://www.stats.gov.cn/sj/zxfb/202312/t20231229_1946084.html', 2023: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202412/t20241231_1958124.html', 2024: 'https://www.stats.gov.cn/zwfwck/sjfb/202512/t20251231_1962228.html'}

def report(year, keyword=''):
    if int(year) not in URLS:
        raise ValueError('仅支持 2022—2024 年')
    u = URLS[int(year)]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', u], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局体育产业公告读取失败（curl %s）' % r.returncode)
    h = r.stdout.decode('utf-8')
    if f'{year}年全国体育产业总规模与增加值数据公告' not in h:
        raise RuntimeError('公告标题无法核验')
    p = _LeafTables()
    p.feed(h)
    tables = [t for t in p.tables if len(t) >= 5 and any(('分类名称' in c['text'] for c in t[0])) and any(('增加值' in c['text'] for c in t[0]))]
    if len(tables) == 2 and tables[0] == tables[1]:
        tables = tables[:1]
    if len(tables) != 1 or len(tables[0]) != 16:
        raise RuntimeError('无法唯一识别体育产业统计表')
    table = tables[0]
    rows = [{'source_row': i + 1, 'cells': row} for i, row in enumerate(table) if i >= 2 and (not keyword or any((keyword in c['text'] for c in row)))]
    return {'source': '国家统计局全国体育产业总规模与增加值数据公告', 'year': int(year), 'url': u, 'header': table[:2], 'rows': rows, 'note': '单位亿元、比重和增速单位为百分比；分组与合计可能因舍入不等。2023 年公告根据第五次经济普查结果核算，跨年比较需核对修订和统计口径。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
