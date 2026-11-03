"""交通运输部全国城市客运量：读取官方 XLSX 附件的原始表格。"""
import release_runtime
import argparse
import datetime
import io
import json
import re
from urllib.parse import urlparse
import openpyxl
import requests
from transport_adapters import transport_detail
FILEPATH = re.compile('^/jigou/zhghs/\\d{6}/P\\d+\\.xlsx$', re.I)

def table(report_url, sheet=None, keyword=''):
    info = transport_detail(report_url)
    files = [x for x in info['attachment_urls'] if urlparse(x).scheme == 'https' and urlparse(x).hostname == 'xxgk.mot.gov.cn' and FILEPATH.fullmatch(urlparse(x).path)]
    if len(files) != 1:
        raise ValueError('未找到唯一的官方 XLSX 附件，不推断其他格式')
    r = requests.get(files[0], timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if urlparse(r.url).hostname != 'xxgk.mot.gov.cn' or urlparse(r.url).scheme != 'https':
        raise ValueError('附件跳转至非原站 HTTPS')
    book = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True, read_only=False)
    if sheet is None:
        sheet = book.sheetnames[0]
    if sheet not in book.sheetnames:
        raise ValueError('工作表不存在')
    ws = book[sheet]
    rows = []
    for line in ws.iter_rows():
        values = [v.value.isoformat() if isinstance(v.value, (datetime.datetime, datetime.date)) else v.value for v in line]
        if not any((v is not None for v in values)):
            continue
        if keyword and (not any((keyword in str(v).replace(' ', '') for v in values if v is not None))):
            continue
        rows.append({'row': line[0].row, 'values': values})
    return {'report_url': report_url, 'report_title': info['title'], 'attachment_url': files[0], 'sheets': book.sheetnames, 'sheet': sheet, 'merged_cells': [str(x) for x in ws.merged_cells.ranges], 'filter_scope': '仅表格当前行原值；筛选时表头和说明可能不包含', 'rows': rows}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report_url')
    p.add_argument('--sheet')
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(table(a.report_url, a.sheet, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
