"""国家统计局第三次全国时间利用调查分组数据表。"""
import release_runtime
import argparse
import json
import subprocess
from moe_education_statistics_adapters import _LeafTables
URL = 'https://www.stats.gov.cn/zt_18555/zthd/lhfw/2025/2025_qgsjlydc/202501/t20250127_1958534.html'

def time_use_2024(table=0):
    if not isinstance(table, int) or isinstance(table, bool) or (not 0 <= table <= 2):
        raise ValueError('表号为 0（全部）、1（日均时间）或 2（参与率）')
    html = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', URL], capture_output=True, check=True).stdout.decode('utf-8')
    if '第三次全国时间利用调查' not in html or '参与者每日平均时间' not in html:
        raise ValueError('未识别调查说明')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 4 and tables[0] == tables[2] and (tables[1] == tables[3]):
        tables = tables[:2]
    if len(tables) != 2:
        raise ValueError('上游表格数量或重复结构变化')
    if '主要活动领域' not in ''.join((c['text'] for c in tables[0][0])) or not any(('单位' in c['text'] and '%' in c['text'] for c in tables[1][0])):
        raise ValueError('未识别原始表头及单位')
    result = [{'table': i + 1, 'title': title, 'rows': t} for i, (title, t) in enumerate(zip(['参与者每日平均时间', '活动参与率'], tables)) if table in (0, i + 1)]
    return {'source_url': URL, 'survey': '第三次全国时间利用调查', 'fieldwork': '2024-05-11 至 2024-05-31', 'tables': result, 'note': '保留原始分组、单位行与注释；时间是参与该项活动的人群平均，不可将不同行时间简单相加为全天；参与率分母、年龄及同时间多活动定义需查原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(time_use_2024(a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
