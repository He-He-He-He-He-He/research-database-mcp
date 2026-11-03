"""民航局2024年机场生产统计公报分省客运吞吐量表。"""
import release_runtime
import hashlib, re
import requests
URL = 'https://www.caac.gov.cn/XXGK/XXGK/TJSJ/202503/P020250314353469776556.pdf'
REGIONS = '广东 上海 北京 四川 浙江 云南 山东 江苏 福建 陕西 重庆 海南 新疆 辽宁 湖北 湖南 河南 内蒙古 黑龙江 贵州 广西 山西 甘肃 吉林 天津 江西 安徽 河北 宁夏 青海 西藏'.split()

def data(year=None, region=None):
    if year is not None and (isinstance(year, bool) or year not in (2023, 2024)):
        raise ValueError('仅支持2023或2024')
    if region is not None and region not in REGIONS + ['全国合计']:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装 PyMuPDF') from e
    r = requests.get(URL, timeout=40)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    d = fitz.open(stream=raw, filetype='pdf')
    a = d[2].get_text()
    b = d[3].get_text()
    title = '表1 各省（区、市）旅客吞吐量及增速'
    if title not in a or '四、货邮吞吐量分布' not in b:
        raise ValueError('未定位原表')
    t = a.split(title, 1)[1] + b.split('四、货邮吞吐量分布', 1)[0]
    lines = [re.sub('\\s+', '', x) for x in t.splitlines() if x.strip()]
    values = {}
    for i, x in enumerate(lines):
        if x == '全国合计':
            v = lines[i + 1:i + 4]
            if len(v) != 3 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', n) for n in v)):
                raise ValueError('全国数据异常')
            values[x] = (None, *map(float, v))
        elif x in REGIONS:
            v = lines[i + 1:i + 5]
            if len(v) != 4 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', n) for n in v)):
                raise ValueError('省级数据异常')
            values[x] = (int(v[0]), *map(float, v[1:]))
    if set(values) != set(REGIONS + ['全国合计']):
        raise ValueError('地区行缺失或变化')
    if sorted((v[0] for k, v in values.items() if k != '全国合计')) != list(range(1, 32)):
        raise ValueError('排名不完整')
    rows = []
    for name in ['全国合计'] + REGIONS:
        if region and name != region:
            continue
        rank, n2024, n2023, growth = values[name]
        for y, n in ((2023, n2023), (2024, n2024)):
            if year is None or year == y:
                rows.append({'region': name, 'year': y, 'passenger_throughput_万人次': n, 'rank_2024': rank, 'growth_2024_percent': growth})
    return {'source': '中国民航局《2024年民航机场生产统计公报》', 'table': title, 'source_url': URL, 'pdf_pages': [3, 4], 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '机场旅客吞吐量单位为万人次，非独立旅客数；排名与增长率均属2024年，2023年值来自同一2024版公报。仅境内运输机场，统计范围和口径以公报为准。', 'rows': rows}
