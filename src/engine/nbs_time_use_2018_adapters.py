"""国家统计局2018年时间利用调查公报三张附表。"""
import release_runtime
import argparse
import json
import requests
from bs4 import BeautifulSoup
from moe_education_statistics_adapters import _LeafTables
URL = 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1900224.html'
NAMES = ['居民主要活动平均时间', '居民主要活动参与率', '居民主要活动参与者平均时间']

def report(table=0):
    if table not in range(4):
        raise ValueError('表号为 0（全部）或 1—3')
    r = requests.get(URL, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if r.url != URL:
        raise ValueError('报告地址发生跳转')
    r.encoding = 'utf8'
    if '2018年全国时间利用调查公报' not in r.text:
        raise ValueError('报告标题未匹配')
    p = _LeafTables()
    p.feed(r.text)
    t = p.tables
    if len(t) == 6 and t[:3] == t[3:]:
        t = t[:3]
    if len(t) != 3:
        raise ValueError('表格数量变化')
    s = BeautifulSoup(r.text, 'html.parser')
    b = s.select_one('.txt-content')
    return {'source_url': URL, 'survey_year': 2018, 'tables': [{'number': i + 1, 'title': NAMES[i], 'rows': x} for i, x in enumerate(t) if table in (0, i + 1)], 'report_text': b.get_text('\n', strip=True) if b else None, 'note': '调查对象为抽中住户中15周岁及以上常住成员；覆盖11个省（市），共调查48580人，不能等同全国全年龄人口。总体平均、参与率、参与者平均是不同分母；与覆盖范围、年龄结构不同的调查比较须核对口径。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(report(a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
