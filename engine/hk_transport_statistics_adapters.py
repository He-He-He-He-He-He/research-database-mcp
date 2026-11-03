"""香港运输署官方交通运输资料摘要原表：年度指标及每月运营商客运。"""
import release_runtime
import argparse
import csv
import io
import json
import re
import requests
TABLES = {'annual_indicators': ('https://www.td.gov.hk/datagovhk_tis/mttd-csv/sc/table11_sc.csv', '年度交通关键指标原表'), 'monthly_operators': ('https://www.td.gov.hk/datagovhk_tis/mttd-csv/en/table21s_eng.csv', '按运营商划分的公共交通平均每日乘客人次原表')}

def transport_statistics(table='annual_indicators', period=None, timeout=15):
    if table not in TABLES:
        raise ValueError('不支持的表')
    if period is not None and (not re.fullmatch('\\d{4}' if table == 'annual_indicators' else '\\d{6}', period)):
        raise ValueError('年度表用 YYYY；月度表用 YYYYMM')
    url, description = TABLES[table]
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    reader = csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')))
    if not reader.fieldnames or reader.fieldnames[0] != ('年份' if table == 'annual_indicators' else 'YR_MTH'):
        raise ValueError('官方表结构异常')
    rows = list(reader)
    key = reader.fieldnames[0]
    if period is not None:
        rows = [r for r in rows if r.get(key) == period]
    return {'source': '香港运输署交通运输资料摘要', 'source_url': url, 'table': table, 'description': description, 'period_filter': period, 'columns': reader.fieldnames, 'rows': rows, 'note': '保留原表字段、数值和注释；单位、符号及统计口径请核对官方原表。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('table', choices=TABLES)
    p.add_argument('--period')
    args = p.parse_args()
    print(json.dumps(transport_statistics(args.table, args.period), ensure_ascii=False, indent=2))
