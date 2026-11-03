"""全国水资源 2024—2025 年已核验公报摘要数值。"""
import release_runtime
DATA = {2024: {'source': 'https://slqjd.mwr.gov.cn/upload/2025/08-08/14-53-240096592685266.pdf', 'source_type': '水利部公报 PDF 第 6 页', 'resources': 31123.0, 'surface': 29895.6, 'groundwater': 8679.2, 'nonoverlap': 1227.4, 'supply': 5928.0, 'use': 5928.0, 'domestic': 926.8, 'industrial': 971.0, 'agriculture': 3648.4, 'ecological': 381.8}, 2025: {'source': 'https://www.gov.cn/lianbo/202606/content_7073826.htm', 'source_type': '中国政府网转载新华社对水利部公报报道', 'resources': 27229.3, 'surface': 26034.0, 'groundwater': 8105.6, 'nonoverlap': 1195.3, 'supply': 5944.5, 'use': 5944.5, 'domestic': 936.6, 'industrial': 953.7, 'agriculture': 3683.8, 'ecological': 370.4}}
NAMES = {'resources': '水资源总量', 'surface': '地表水资源量', 'groundwater': '地下水资源量', 'nonoverlap': '地下水与地表水不重复量', 'supply': '供水总量', 'use': '用水总量', 'domestic': '生活用水量', 'industrial': '工业用水量', 'agriculture': '农业用水量', 'ecological': '人工生态环境补水量'}

def water_bulletins(year=None):
    if year is not None:
        year = int(year)
        if year not in DATA:
            raise ValueError('目前仅覆盖 2024 与 2025')
    records = []
    for y, d in sorted(DATA.items()):
        if year is not None and year != y:
            continue
        records.append({'year': y, 'source': d['source'], 'source_type': d['source_type'], 'unit': '亿立方米', 'data': {name: d[key] for key, name in NAMES.items()}})
    return {'coverage': '2024—2025 全国公报摘要', 'results': records, 'note': '水资源量为当年评价量，供用水量为年度流量；各统计指标不可混为水库蓄水量。2025 年为政府网报道，不是公报全文。'}
