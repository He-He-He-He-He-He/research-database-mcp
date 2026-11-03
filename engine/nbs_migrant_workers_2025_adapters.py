"""国家统计局 2025 年农民工监测调查报告原表。"""
import release_runtime
import argparse
import json
import subprocess
from moe_education_statistics_adapters import _LeafTables
URL = 'https://www.stats.gov.cn/sj/zxfb/202604/t20260430_1963472.html'
TITLES = ['2025年外出农民工地区分布及构成', '农民工输出和输入地区分布', '农民工年龄构成', '农民工就业行业分布情况', '分行业农民工月均收入及增速']

def migrant_worker_report(table=0):
    if not isinstance(table, int) or isinstance(table, bool) or (not 0 <= table <= 5):
        raise ValueError('表号为 0（全部）或 1–5')
    raw = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', URL], capture_output=True, check=True).stdout.decode('utf-8')
    if '2025年农民工监测调查报告' not in raw:
        raise ValueError('报告标题无法验证')
    p = _LeafTables()
    p.feed(raw)
    tables = p.tables
    if len(tables) == 10 and all((tables[i] == tables[i + 5] for i in range(5))):
        tables = tables[:5]
    if len(tables) != 5:
        raise ValueError('上游表数量或重复结构变化')
    if any((not t or not any(('单位' in c['text'] for c in t[0])) for t in tables)):
        raise ValueError('未识别表格单位')
    rows = [{'table': i + 1, 'title': TITLES[i], 'rows': t} for i, t in enumerate(tables) if table in (0, i + 1)]
    return {'source_url': URL, 'reference_year': 2025, 'tables': rows, 'note': '原表保留单位、分组和合并单元格；农民工按农村户籍及非农/外出就业时间界定；总体、外出和行业等分母不同；保留空白，不视为零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(migrant_worker_report(a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
