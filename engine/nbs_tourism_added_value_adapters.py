"""国家统计局全国旅游及相关产业增加值分类原表。"""
import release_runtime
import json, subprocess
from moe_education_statistics_adapters import _LeafTables
URLS = {2020: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202112/t20211229_1825727.html', 2021: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202212/t20221230_1891329.html', 2022: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202312/t20231229_1946075.html', 2023: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202412/t20241230_1957935.html', 2024: 'https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202512/t20251230_1962180.html'}

def report(year, keyword=''):
    if int(year) not in URLS:
        raise ValueError('仅支持 2020—2024 年')
    u = URLS[int(year)]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', u], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局公告读取失败（curl %s）' % r.returncode)
    html = r.stdout.decode('utf8')
    if f'{year}年全国旅游及相关产业增加值' not in html:
        raise RuntimeError('无法核验公告年份和主题')
    p = _LeafTables()
    p.feed(html)
    candidates = []
    for t in p.tables:
        for i, row in enumerate(t[:3]):
            if any(('分类名称' in c['text'] for c in row)) and any(('增加值' in c['text'] for c in row)):
                candidates.append((t, i))
                break
    if len(candidates) == 2 and candidates[0] == candidates[1]:
        candidates = candidates[:1]
    if len(candidates) != 1:
        raise RuntimeError('未唯一识别旅游产业增加值表')
    table, idx = candidates[0]
    rows = [{'source_row': i + 1, 'cells': row} for i, row in enumerate(table) if i > idx and len(row) > 1 and any((c['text'] for c in row)) and (not keyword or any((keyword in c['text'] for c in row)))]
    notes = [row for row in table[idx + 1:] if len(row) == 1 and row[0]['text']]
    return {'source': '国家统计局全国旅游及相关产业增加值公告', 'year': int(year), 'url': u, 'header': table[:idx + 1], 'rows': rows, 'note_rows': notes, 'note': '增加值单位亿元，构成为百分比；2020—2022 表含现价增速、2023—2024 不含。2023 依第五次经济普查核算，跨年比较须核对修订及官网附注；增加值不等于营业收入。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
