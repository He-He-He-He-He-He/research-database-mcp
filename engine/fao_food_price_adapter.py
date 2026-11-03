"""FAO 世界食品价格指数月度官方公开 CSV。"""
import release_runtime
import csv, io, re
import requests
URL = 'https://www.fao.org/media/docs/worldfoodsituationlibraries/wfs-library/food_price_indices_data.csv'

def food_price_index(start='1990-01', end=None, limit=24, offset=0):
    for v in (start, end):
        if v is not None and (not isinstance(v, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', v)):
            raise ValueError('月份应为 YYYY-MM')
    if start and end and (start > end):
        raise ValueError('开始月份不能晚于结束月份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit 应为 1 至 500')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('offset 应为 0 至 100000 的整数')
    r = requests.get(URL, timeout=25)
    r.raise_for_status()
    rows = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
    header = ['Date', 'Food Price Index', 'Meat', 'Dairy', 'Cereals', 'Oils', 'Sugar']
    if len(rows) < 4 or rows[1][0].strip() != '2014-2016=100' or rows[2][:7] != header:
        raise RuntimeError('FAO 指数 CSV 结构或基期已变化')
    items = []
    for row in rows[3:]:
        if not row or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', row[0].strip()):
            continue
        if len(row) < 7:
            raise RuntimeError('FAO 指数 CSV 数据行不完整')
        month = row[0].strip()
        if start and month < start or (end and month > end):
            continue
        items.append(dict(zip(header, [x.strip() for x in row[:7]])))
    items.sort(key=lambda x: x['Date'], reverse=True)
    selected = items[offset:offset + limit]
    return {'source': '联合国粮农组织 FAO 食品价格指数官方月度 CSV', 'start': start, 'end': end, 'total_matching': len(items), 'limit': limit, 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(items) else None, 'truncated': offset + len(selected) < len(items), 'items': selected, 'scope': '结果按月份倒序；offset 为本地位置，每次重取 CSV，发布新月份后位置可能移动，旧值也可能修订。2014–2016=100；全球一篮子食品大宗商品国际名义价格指数，包含肉类、乳制品、谷物、植物油和糖，不是国内零售价格。', 'download_url': URL, 'documentation': 'https://www.fao.org/worldfoodsituation/foodpricesindex/en/'}
