"""国家邮政局全国邮政行业运行情况公开原表。"""
import release_runtime
import json, subprocess
from cnipa_stats_adapters import Tables
REPORTS = {'2025-12': {'url': 'https://www.mot.gov.cn/shuju/tongjishuju/youzheng/202601/t20260130_4199355.html', 'titles': ['全国行业发展情况', '分省快递业务情况', '城市快递业务收入前 50 名', '城市快递处理量前 50 名'], 'header_rows': [2, 1, 1, 1]}, '2026-09': {'url': 'https://www.spb.gov.cn/gjyzj/c100015/c100016/202610/d825347972b7427c95a9fe68ff355ce8.shtml', 'titles': ['全国行业发展情况'], 'header_rows': [3]}}

def data(period, table=1, keyword=''):
    if period not in REPORTS:
        raise ValueError('仅支持 2025-12 和 2026-09，请查询目录')
    info = REPORTS[period]
    if not 1 <= int(table) <= len(info['titles']):
        raise ValueError('表号超出该期目录')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', info['url']], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('邮政行业报告读取失败（curl %s）' % p.returncode)
    parser = Tables()
    parser.feed(p.stdout.decode('utf-8'))
    tables = [t for t in parser.tables if len(t) >= 4]
    if len(tables) != len(info['titles']):
        raise RuntimeError('表格数不匹配，原网页可能改变')
    i = int(table) - 1
    rows = tables[i]
    n = info['header_rows'][i]
    if not any(('快递' in c['text'] or '邮政' in c['text'] or '指标' in c['text'] for r in rows[:n] for c in r)):
        raise RuntimeError('表头不符合预期')
    matches = [{'source_row': j + 1, 'cells': r} for j, r in enumerate(rows) if j >= n and (not keyword or any((keyword in c['text'] for c in r)))]
    return {'source': '国家邮政局邮政行业运行情况', 'period': period, 'url': info['url'], 'table': int(table), 'table_title': info['titles'][i], 'header': rows[:n], 'rows': matches, 'note': '保留原表单元格及合并标记。营业收入不含邮政储蓄银行直接营业收入；累计与当月、处理量和业务量等概念不同，单位、口径及附注以原文为准。'}

def catalog():
    return {period: {'url': r['url'], 'tables': [{'number': i + 1, 'title': t} for i, t in enumerate(r['titles'])]} for period, r in REPORTS.items()}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('list')
    q = s.add_parser('data')
    q.add_argument('period', choices=REPORTS)
    q.add_argument('--table', type=int, default=1)
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(catalog() if a.cmd == 'list' else data(a.period, a.table, a.keyword), ensure_ascii=False, indent=2))
