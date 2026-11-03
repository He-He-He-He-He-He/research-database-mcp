"""NASA GISTEMP v4 全球陆海表面温度距平公开数据。"""
import release_runtime
import csv, io
import requests
URL = 'https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def global_temperature(start_year=2000, end_year=None, limit=30):
    if isinstance(start_year, bool) or not isinstance(start_year, int) or (not 1880 <= start_year <= 9999):
        raise ValueError('start_year 必须是 1880 之后的年份')
    if end_year is not None and (isinstance(end_year, bool) or not isinstance(end_year, int) or end_year < start_year or (end_year > 9999)):
        raise ValueError('end_year 无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('limit 必须为 1 至 200')
    r = requests.get(URL, timeout=25)
    r.raise_for_status()
    lines = r.content.decode('utf-8-sig').splitlines()
    if not lines or lines[0].strip() != 'Land-Ocean: Global Means':
        raise RuntimeError('NASA GISTEMP 表头异常')
    reader = csv.DictReader(io.StringIO('\n'.join(lines[1:])))
    if not reader.fieldnames or not {'Year', 'J-D', *MONTHS}.issubset(reader.fieldnames):
        raise RuntimeError('NASA GISTEMP 列结构异常')
    rows = []
    for x in reader:
        try:
            year = int(x['Year'])
        except (ValueError, TypeError):
            raise RuntimeError('NASA 年份格式异常') from None
        if year < start_year or (end_year is not None and year > end_year):
            continue

        def read(v):
            return None if not v or v.strip() == '***' else v.strip()
        rows.append({'year': year, 'months': {m: read(x[m]) for m in MONTHS}, 'annual': read(x['J-D']), 'seasons': {k: read(x[k]) for k in ('DJF', 'MAM', 'JJA', 'SON')}})
    rows.sort(key=lambda x: x['year'], reverse=True)
    return {'source': 'NASA GISS Surface Temperature Analysis v4 全球陆海温度指数', 'unit': '摄氏度距平，1951–1980 均值为基期', 'total_matching': len(rows), 'limit': limit, 'truncated': len(rows) > limit, 'items': rows[:limit], 'scope': '结果按年份倒序；如 truncated 为 true 可提高 limit（最多200）或缩小年份范围。相对基期的全球平均陆海表面温度变化，不是绝对气温；空值是未公布/缺失，非零；历史值可能修订。', 'download_url': URL, 'documentation': 'https://data.giss.nasa.gov/gistemp/data_v4.html'}
