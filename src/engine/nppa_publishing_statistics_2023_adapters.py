"""国家新闻出版署 2023 年新闻出版统计公报表格。"""
import release_runtime
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2023年新闻出版统计公报.pdf')
SOURCE_URL = 'https://www.nppa.gov.cn/xxgk/fdzdgknr/tjxx/202503/P020250318599786997599.pdf'
TABLES = {1: ('主要经济指标', ['亿元'] * 4), 2: ('图书出版主要指标', ['万种', '万种', '亿册（张）', '亿元', '亿元']), 3: ('报纸出版主要指标', ['种', '亿份', '亿元', '亿元']), 4: ('期刊出版主要指标', ['种', '亿册', '亿元', '亿元']), 5: ('音像制品出版主要指标', ['种', '万盒（张）', '亿元', '亿元']), 6: ('电子出版物出版主要指标', ['种', '万张', '亿元', '亿元']), 7: ('印刷复制主要指标', ['万令', '万对开色令', '亿元', '亿元']), 8: ('出版物发行主要指标', ['亿册（份、盒、张）', '亿元', '亿元']), 9: ('全国出版物进出口主要指标', ['万册（份、盒、张）', '万美元', '万册（份、盒、张）', '万美元', '亿元', '亿元']), 10: ('版权管理服务与出版物版权贸易主要指标', ['份', '份', '项', '项'])}

def publishing_statistics_2023(table=None, keyword=''):
    """查询 10 个原表；数值为原文十进制字符串，增长单位为百分比。"""
    if table is not None and table not in TABLES:
        raise ValueError('table 应为 1 至 10')
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 7:
        raise ValueError('原 PDF 页数异常')
    result = []
    current = None
    row_index = 0
    counts = {k: 0 for k in TABLES}
    header = re.compile('^表\\s*(\\d+)\\s+')
    numeric_row = re.compile('^(.+?)\\s+(-?\\d+(?:\\.\\d+)?)\\s+(-?\\d+(?:\\.\\d+)?)\\s+(-?\\d+(?:\\.\\d+)?)\\s*$')
    for page_no, page in enumerate(reader.pages, 1):
        for line in (page.extract_text() or '').splitlines():
            line = line.strip()
            h = header.match(line)
            if h:
                current = int(h.group(1))
                row_index = 0
                if current not in TABLES:
                    raise ValueError('未知表编号')
                continue
            if current is None:
                continue
            m = numeric_row.match(line)
            if not m:
                continue
            if row_index >= len(TABLES[current][1]):
                raise ValueError('数据行数超出预期')
            label, prev, now, growth = m.groups()
            name, units = TABLES[current]
            result.append({'table': current, 'table_name': name, 'indicator': re.sub('\\s+', '', label), 'unit': units[row_index], '2022': prev, '2023': now, 'change_percent': growth, 'pdf_page': page_no, 'source_url': SOURCE_URL})
            counts[current] += 1
            row_index += 1
    if any((counts[n] != len(TABLES[n][1]) for n in TABLES)):
        raise ValueError(f'原表行数异常: {counts}')
    keyword = keyword.strip()
    return [r for r in result if (table is None or r['table'] == table) and (not keyword or keyword in r['indicator'] or keyword in r['table_name'])]
