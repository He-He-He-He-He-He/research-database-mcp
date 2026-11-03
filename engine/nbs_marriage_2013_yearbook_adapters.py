"""中国统计年鉴2014婚姻服务原表：历史年度及2013地区数据。"""
import release_runtime
import argparse
import json
import sys
from pathlib import Path
FILE = Path(__file__).parent / '数据/中国统计年鉴2014/22-33婚姻服务情况.xls'
SOURCE = 'https://www.stats.gov.cn/sj/ndsj/2014/zk/html/Z2233C.xls'
TABLE = 'https://www.stats.gov.cn/sj/ndsj/2014/zk/html/Z2233C.HTM'

def rows(keyword=''):
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as e:
            raise RuntimeError('读取 XLS 原表需要安装 xlrd') from e
    sheet = xlrd.open_workbook(str(FILE)).sheet_by_index(0)
    if sheet.ncols != 8 or '婚姻服务情况' not in str(sheet.cell_value(0, 0)):
        raise ValueError('原表结构不符')
    out = []
    for i in range(7, sheet.nrows):
        values = sheet.row_values(i)
        label = values[0]
        if not str(label).strip() or not any((isinstance(v, (float, int)) for v in values[1:])):
            continue
        name = str(int(label)) if isinstance(label, (float, int)) and label == int(label) else str(label).strip()
        if ''.join(keyword.split()) not in ''.join(name.split()):
            continue
        out.append({'source_row': i + 1, 'label': name, 'values': [None if v == '' else v for v in values[1:]]})
    return {'source': SOURCE, 'yearbook': 2014, 'table': TABLE, 'columns': ['结婚登记(万对)', '内地居民登记结婚(万对)', '初婚(万人)', '再婚(万人)', '涉外及港澳台居民登记结婚(万对)', '离婚(万对)', '粗离婚率(‰)'], 'rows': out, 'note': '年度行按标示年份；地区行为2013年。保留XLS底层数值，可能多于网页表显示精度；空值为null。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(rows(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
