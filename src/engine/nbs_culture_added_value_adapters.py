"""国家统计局全国文化及相关产业增加值分类表。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
URLS = {2021: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901697.html', 2022: 'https://www.stats.gov.cn/sj/zxfb/202312/t20231229_1946065.html', 2023: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202412/t20241230_1957934.html', 2024: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202512/t20251230_1962179.html'}

def report(year, keyword=''):
    if int(year) not in URLS:
        raise ValueError('仅支持 2021—2024 年')
    u = URLS[int(year)]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', u], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局公告读取失败（curl %s）' % r.returncode)
    html = r.stdout.decode('utf-8')
    if f'{year}年全国文化及相关产业增加值' not in html:
        raise RuntimeError('未能核验公告年份和主题')
    p = _LeafTables()
    p.feed(html)
    tables = [t for t in p.tables if len(t) >= 10 and any(('分类名称' in c['text'] for c in t[0])) and any(('增加值' in c['text'] for c in t[0]))]
    if len(tables) == 2 and tables[0] == tables[1]:
        tables = tables[:1]
    if len(tables) != 1:
        raise RuntimeError('无法唯一识别文化产业增加值表')
    table = tables[0]
    rows = [{'source_row': i + 1, 'cells': r} for i, r in enumerate(table) if i > 0 and any((c['text'] for c in r)) and (not keyword or any((keyword in c['text'] for c in r)))]
    return {'source': '国家统计局全国文化及相关产业增加值公告', 'year': int(year), 'url': u, 'header': table[0], 'rows': rows, 'note': '增加值单位为亿元、构成为百分比；表中行业和活动性质是不同分类，筛选可能丢失分组。2023年依第五次经济普查结果核算，跨年比较需核对修订口径；增加值不等于营业收入。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
