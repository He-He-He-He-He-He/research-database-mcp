"""2020 年国家卫生健康事业公报公开转载表格快照。"""
import release_runtime
from pathlib import Path
from moe_education_statistics_adapters import _LeafTables
SOURCE = 'https://yueyang.gov.cn/web/2570/2598/3425/content_1868647.html'
PATH = Path(__file__).resolve().parent / '数据' / '国家卫生健康统计公报' / '2020_岳阳市政府转载.html'

def nhc_health_2020_tables():
    """返回公报 HTML 的叶级表格，单元格文字与合并属性保持原样。"""
    parser = _LeafTables()
    parser.feed(PATH.read_bytes().decode('gb18030'))
    if len(parser.tables) != 21 or not parser.tables[0] or parser.tables[0][0][0]['text'] != '机构类别':
        raise ValueError('原始快照表格结构不符合已验证版本')
    return {'report_year': 2020, 'source_url': SOURCE, 'tables': parser.tables, 'note': '年度比较列与单位见各表表头；空值、破折号及合并单元格保留原文，统计口径参看公报正文。'}

def nhc_health_2020_table(number):
    """按原文顺序获取第 1—21 个表格（从 1 开始）。"""
    number = int(number)
    if not 1 <= number <= 21:
        raise ValueError('表格序号应为 1—21')
    result = nhc_health_2020_tables()
    return {'report_year': 2020, 'source_url': SOURCE, 'table_number': number, 'rows': result['tables'][number - 1], 'note': result['note']}
