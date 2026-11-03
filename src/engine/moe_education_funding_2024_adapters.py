"""2024 年全国教育经费执行情况统计表。"""
import release_runtime
from pathlib import Path
import re
ROOT = Path(__file__).parent
TEXT_PATH = ROOT / '2024年全国教育经费执行情况统计表_提取文本.txt'
DOC_PATH = ROOT / '2024年全国教育经费执行情况统计表.doc'
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A05/s3040/202512/t20251231_1426092.html'
DOC_URL = 'https://www.moe.gov.cn/srcsite/A05/s3040/202512/W020260109376441821920.doc'

def education_funding_2024(region=''):
    """查询原表全国和 31 省区市五项指标；数值原样保留为字符串。"""
    lines = [x.strip() for x in TEXT_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    start = next((i for i, line in enumerate(lines) if re.sub('\\s+', '', line) == '全国'), None)
    if start is None:
        raise ValueError('原表全国行未找到')
    result = []
    seen = set()
    i = start
    num = re.compile('^-?\\d+(?:\\.\\d+)?$')
    while i < len(lines):
        region_name = re.sub('\\s+', '', lines[i])
        if not (region_name == '全国' or region_name.endswith(('省', '市', '自治区'))):
            break
        values = lines[i + 1:i + 6]
        if len(values) != 5 or not all((num.fullmatch(v) for v in values)) or region_name in seen:
            raise ValueError(f'地区行解析异常: {region_name}')
        result.append({'region': region_name, 'year': 2024, 'budget_education_yi_yuan': values[0], 'budget_growth_percent': values[1], 'share_of_public_budget_percent': values[2], 'per_student_yuan': values[3], 'per_student_growth_percent': values[4], 'source_url': SOURCE_URL, 'doc_url': DOC_URL})
        seen.add(region_name)
        i += 6
    if len(result) != 32:
        raise ValueError(f'地区行数异常: {len(result)}')
    region = region.strip()
    return [r for r in result if not region or region in r['region']]
