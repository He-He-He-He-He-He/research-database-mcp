"""国家能源局全国电力工业统计数据 HTML 原表。"""
import release_runtime
import json, subprocess
from cnipa_stats_adapters import Tables
REPORTS = {'2024-12': 'https://www.nea.gov.cn/20250121/097bfd7c1cd3498897639857d86d5dac/c.html', '2025-03': 'https://www.nea.gov.cn/20250420/ea90b16331c446a1bad218c4b3c0df7d/c.html', '2025-04': 'https://www.nea.gov.cn/20250522/ba33708cb5e749378a21c955170069c1/c.html', '2025-06': 'https://www.nea.gov.cn/20250723/d7a5d6cc916e40bcb04c7d7e74d03213/c.html', '2025-08': 'https://www.nea.gov.cn/20250926/2e8ea0184702461f8531527b015964d5/c.html', '2025-09': 'https://www.nea.gov.cn/20251026/70d3b88f62f1401bbe47a8212e06ad8e/c.html', '2025-10': 'https://www.nea.gov.cn/20251125/c08a5f9b4a54481696a432ecd6c70dd3/c.html'}

def report(period, keyword=''):
    if period not in REPORTS:
        raise ValueError('不支持该期，先查询 periods')
    url = REPORTS[period]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('国家能源局报告读取失败（curl %s）' % p.returncode)
    parser = Tables()
    parser.feed(p.stdout.decode('utf-8'))
    tables = [t for t in parser.tables if any(('全国发电装机容量' in c['text'] for row in t for c in row))]
    if len(tables) != 1:
        raise RuntimeError('未唯一识别发电统计表，请核对官网页面')
    rows = tables[0]
    header_end = next((i for i, r in enumerate(rows[:3]) if any((c['text'] == '单位' for c in r)) and any(('同比' in c['text'] for c in r))), None)
    if header_end is None:
        raise RuntimeError('无法识别表头')
    selected = [{'source_row': i + 1, 'cells': r} for i, r in enumerate(rows) if i > header_end and (not keyword or any((keyword in c['text'] for c in r)))]
    return {'source': '国家能源局全国电力工业统计数据', 'period': period, 'url': url, 'header': rows[:header_end + 1], 'rows': selected, 'note': '原表单元格与合并属性原样返回；累计装机为报告期末存量，利用小时和投资为当年累计。同比列中 * 标记表示绝对量、▲ 标记表示百分点；筛选单行可能失去所属分组，请核对全表与官网附注。'}

def periods():
    return [{'period': k, 'url': v} for k, v in REPORTS.items()]
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('periods')
    q = s.add_parser('report')
    q.add_argument('period', choices=REPORTS)
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(periods() if a.cmd == 'periods' else report(a.period, a.keyword), ensure_ascii=False, indent=2))
