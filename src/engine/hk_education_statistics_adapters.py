"""香港教育局公开在校生统计原表。"""
import release_runtime
import argparse
import csv
import io
import json
import requests
TABLES = {'level_sex': ('https://www.edb.gov.hk/attachment/sc/about-edb/publications-stat/figures/enrol-by-level-sex_SC.csv', '按学年、教育层级与性别的在校生，单位千人'), 'primary_district': ('https://www.edb.gov.hk/attachment/sc/about-edb/publications-stat/figures/tab0307_sc.csv', '按地区和年级的小学生人数；该 CSV 未标明学年')}

def education_statistics(table='level_sex', keyword=None, timeout=15):
    if table not in TABLES:
        raise ValueError('不支持的表')
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('筛选词无效')
    url, description = TABLES[table]
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')))
    expected = '学年' if table == 'level_sex' else '分区'
    if not reader.fieldnames or reader.fieldnames[0] != expected:
        raise ValueError('官方 CSV 表头已变化')
    rows = list(reader)
    if keyword is not None:
        rows = [r for r in rows if any((keyword in str(v or '') for v in r.values()))]
    return {'source': '香港教育局公开统计', 'source_url': url, 'table': table, 'description': description, 'keyword_filter': keyword, 'columns': reader.fieldnames, 'rows': rows, 'note': '原始字段和备注保留；分区总计与其子区不可重复相加，空值不等于零。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('table', choices=TABLES)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(education_statistics(a.table, a.keyword), ensure_ascii=False, indent=2))
