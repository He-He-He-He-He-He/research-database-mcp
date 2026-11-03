"""国家统计局全国文化及相关产业年度发展情况报告表格。"""
import release_runtime
import json, subprocess
from cnipa_stats_adapters import Tables
REPORTS = {2022: 'https://www.stats.gov.cn/sj/zxfb/202306/t20230629_1940907.html', 2024: 'https://www.stats.gov.cn/zwfwck/sjfb/202506/t20250627_1960269.html', 2025: 'https://www.stats.gov.cn/zwfwck/sjfb/202606/t20260629_1964025.html'}

def report(year, keyword=''):
    if int(year) not in REPORTS:
        raise ValueError('目前仅支持 2022、2024 或 2025 年报告')
    url = REPORTS[int(year)]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局报告请求失败（curl 状态 %s）' % r.returncode)
    p = Tables()
    p.feed(r.stdout.decode('utf-8'))
    candidates = []
    for table in p.tables:
        values = ' '.join((c['text'] for row in table for c in row))
        if '营业收入' in values and '资产总计' in values and (len(table) >= 5):
            candidates.append(table)
    if len(candidates) == 2 and candidates[0] == candidates[1]:
        candidates = candidates[:1]
    if len(candidates) != 1:
        raise RuntimeError('未能唯一识别统计表；请核对原文')
    rows = candidates[0]
    selected = [{'source_row': i + 1, 'cells': row} for i, row in enumerate(rows[3:], start=3) if not keyword or any((keyword in c['text'] for c in row))]
    return {'source': '国家统计局全国文化及相关产业发展情况报告', 'year': int(year), 'url': url, 'header': rows[:3], 'rows': selected, 'note': '年度统计包含规模以上及规模以下文化产业法人单位，范围不同于规模以上企业数据；保留合并单元格，具体单位、可比口径与表下注释以官网原文为准。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(REPORTS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
