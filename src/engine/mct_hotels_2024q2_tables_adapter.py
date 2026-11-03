"""MOCT 2024 Q2 hotel tables republished by China Tourism News."""
import release_runtime
import io
import requests
import openpyxl
ARTICLE = 'https://www.ctnews.com.cn/jujiao/content/2024-09/04/content_164307.html'
OFFICIAL = 'https://zwgk.mct.gov.cn/zfxxgkml/tjxx/202409/t20240902_955009.html'
BASE = 'https://www.ctnews.com.cn/jujiao/att/2024-09/04/'
TABLES = {'regional': ('全国星级饭店经营情况', 'ff6fa129-4a65-4f20-b84a-529dc4f6379f'), 'regional_star': ('全国星级饭店经营情况按星级分', '9af7c9e1-e869-4901-922d-1758c207b94e'), 'cities': ('50个重点旅游城市星级饭店经营情况', 'b6856fc0-d4ba-41a5-8504-161868cf58bf'), 'cities_star': ('50个重点旅游城市星级饭店经营情况按星级分', '23ca2865-e586-4ebf-9b1f-749a7295dbb3')}

def catalog():
    return [{'code': k, 'title': v[0], 'url': BASE + v[1] + '.xlsx', 'author': '文化和旅游部', 'publisher': '中国旅游新闻网转载'} for k, v in TABLES.items()]

def read(code, keyword='', limit=100):
    if code not in TABLES:
        raise ValueError('未知表格代码')
    if not 1 <= int(limit) <= 500:
        raise ValueError('limit 应为 1 至 500')
    url = BASE + TABLES[code][1] + '.xlsx'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise RuntimeError('响应不是 XLSX 文件')
    book = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True, read_only=True)
    ws = book.active
    rows = [list(row) for row in ws.iter_rows(values_only=True)]
    book.close()
    matches = [{'row': i + 1, 'cells': row} for i, row in enumerate(rows) if keyword and any((keyword in str(v) for v in row if v is not None))]
    return {'source_url': url, 'source_article': ARTICLE, 'official_page': OFFICIAL, 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'sheet': ws.title, 'headers': rows[:3], 'matches': len(matches) if keyword else len(rows), 'rows': matches[:int(limit)] if keyword else [{'row': i + 1, 'cells': row} for i, row in enumerate(rows[:int(limit)])], 'note': '保留原始单元格；空值不作零，合并标题须看原表。仅统计通过审核的星级饭店。'}
