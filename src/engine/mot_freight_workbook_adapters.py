"""交通运输部公路水路运输量 XLSX 原表读取。"""
import release_runtime
import hashlib
import re
import subprocess
from io import BytesIO
from openpyxl import load_workbook
from freight_adapters import freight_list, freight_detail

def table(url):
    """从现有目录返回的详情链接读取运输量表，保留官方表头、空值。"""
    d = freight_detail(url)
    title = d['title']
    items = [u for u in d['attachment_urls'] if re.fullmatch('https://xxgk\\.mot\\.gov\\.cn/jigou/zhghs/\\d{6}/P\\d+\\.xlsx', u)]
    if len(items) != 1:
        raise RuntimeError('未识别唯一运输量 XLSX 附件')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '15000000', items[0]], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('交通运输部原表请求失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    raw = p.stdout
    if len(raw) > 15000000:
        raise RuntimeError('原表超过 15 MB')
    book = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    if '运输量' not in book.sheetnames:
        raise RuntimeError('未识别运输量工作表')
    sheet = book['运输量']
    data = list(sheet.iter_rows(min_row=1, max_col=9, values_only=True))
    if not data or '公路水路运输量' not in str(data[0][0]):
        raise RuntimeError('表格标题不符')
    rows = []
    notes = []
    for i, r in enumerate(data[5:], 6):
        if isinstance(r[0], str) and r[0].strip():
            if r[0].strip().startswith(('注：', '注:')):
                notes.append(r[0])
            else:
                rows.append({'row': i, 'region': r[0], 'values': list(r[1:9])})
    if not rows or not re.sub('\\s+', '', rows[0]['region']) == '总计':
        raise RuntimeError('未识别总计行')
    return {'source_page': url, 'title': title, 'workbook_url': items[0], 'sha256': hashlib.sha256(raw).hexdigest(), 'sheet': '运输量', 'headers': [list(r[:9]) for r in data[2:5]], 'rows': rows, 'notes': notes, 'note': '按原表顺序分别为公路客运、水路客运、公路货运、水路货运，各含年初累计和同比增速；表头和空值须核对。'}
