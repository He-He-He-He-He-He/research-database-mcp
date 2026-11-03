"""国家统计局“三新”经济增加值核算结果原表。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
URLS = {2022: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202307/t20230728_1941592.html', 2023: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202407/t20240730_1955890.html', 2024: 'https://www.stats.gov.cn/sj/zxfbhjd/202507/t20250731_1960553.html', 2025: 'https://www.stats.gov.cn/sj/zxfbhjd/202607/t20260730_1964247.html'}

def report(year, keyword=''):
    if int(year) not in URLS:
        raise ValueError('仅支持 2022—2025 年')
    u = URLS[int(year)]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', u], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局公告读取失败（curl %s）' % r.returncode)
    h = r.stdout.decode('utf8')
    if str(year) + '年' not in h or '“三新”经济增加值' not in h:
        raise RuntimeError('未能核验公告年份和主题')
    p = _LeafTables()
    p.feed(h)
    tables = [t for t in p.tables if len(t) >= 5 and any(('增加值' in c['text'] for c in t[0])) and any(('产业' in c['text'] for c in t[0]))]
    if len(tables) == 2 and tables[0] == tables[1]:
        tables = tables[:1]
    if len(tables) != 1:
        raise RuntimeError('未唯一识别核算结果表')
    table = tables[0]
    rows = [{'source_row': i + 1, 'cells': row} for i, row in enumerate(table) if i > 0 and len(row) > 1 and (not keyword or any((keyword in c['text'] for c in row)))]
    notes = [row for row in table[1:] if len(row) == 1]
    return {'source': '国家统计局“三新”经济增加值核算结果', 'year': int(year), 'url': u, 'header': table[0], 'rows': rows, 'note_rows': notes, 'note': '增加值按现价计，增长率未扣价格因素；构成为“三新”经济内部比例，不是占GDP比重。跨年比较需核对经济普查修订及官网附注，增速与绝对值不能忽略口径变化。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
