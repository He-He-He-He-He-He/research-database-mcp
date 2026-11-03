"""第三次全国时间利用调查全国活动领域与大类原表。"""
import release_runtime
import argparse
import json
import subprocess
from moe_education_statistics_adapters import _LeafTables
URL = 'https://www.stats.gov.cn/zt_18555/zthd/lhfw/2025/2025_qgsjlydc/202501/t20250127_1958535.html'

def time_use_totals_2024(table=0):
    if not isinstance(table, int) or isinstance(table, bool) or (not 0 <= table <= 2):
        raise ValueError('表号为 0（全部）、1（活动领域）或 2（活动大类）')
    html = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', URL], capture_output=True, check=True).stdout.decode('utf-8')
    if '第三次全国时间利用调查' not in html or '活动参与率' not in html:
        raise ValueError('未识别调查说明')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 4 and tables[0] == tables[2] and (tables[1] == tables[3]):
        tables = tables[:2]
    if len(tables) != 2:
        raise ValueError('上游表格数量或重复结构变化')
    if not any(('主要活动领域' in c['text'] for c in tables[0][0])) or not any(('主要活动大类' in c['text'] for c in tables[1][0])):
        raise ValueError('未识别原始表头')
    result = [{'table': i + 1, 'title': title, 'rows': t} for i, (title, t) in enumerate(zip(['主要活动领域', '主要活动大类'], tables)) if table in (0, i + 1)]
    return {'source_url': URL, 'survey': '第三次全国时间利用调查', 'fieldwork': '2024-05-11 至 2024-05-31', 'tables': result, 'note': '调查范围为31个省（区、市）及新疆生产建设兵团，首次增加6—14周岁人员；与2018年调查的人群和地区范围不同。居民日均时间与参与者日均时间分母不同，参与率为百分比；活动领域与活动大类不是相同分类，不能无条件相加或用一个类别代替另一类别；保留原表及注释。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(time_use_totals_2024(a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
