"""民航局2023年机场生产公报省级旅客及货邮数据。"""
import release_runtime
import hashlib, re
import requests
URL = 'https://www.caac.gov.cn/XXGK/XXGK/TJSJ/202403/P020240320504230898437.pdf'
REGIONS = '北京 上海 天津 陕西 青海 河南 甘肃 内蒙古 新疆 广东 山西 广西 辽宁 四川 福建 吉林 湖北 江苏 海南 江西 山东 湖南 黑龙江 浙江 安徽 云南 宁夏 西藏 重庆 贵州 河北'.split()

def data(metric, year=None, region=None):
    if metric not in ('passenger', 'cargo'):
        raise ValueError('指标为 passenger 或 cargo')
    if year is not None and (isinstance(year, bool) or year not in (2022, 2023)):
        raise ValueError('仅支持2022或2023')
    if region is not None and region not in REGIONS + ['全国合计']:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装PyMuPDF') from e
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    raw = r.content
    if len(raw) > 10000000 or not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    doc = fitz.open(stream=raw, filetype='pdf')
    if metric == 'passenger':
        s = doc[3].get_text()
        title = '表1 各省（区、市）旅客吞吐量及增速'
        end = '四、'
        unit = '万人次'
        pages = [4]
    else:
        s = doc[4].get_text() + doc[5].get_text()
        title = '表2 各省（区、市）货邮吞吐量及增速'
        end = '注：'
        unit = '万吨'
        pages = [5, 6]
    if title not in s:
        raise ValueError('原表标题不存在')
    s = s.split(title, 1)[1].split(end, 1)[0]
    tokens = s.split()
    values = {}
    for i, name in enumerate(tokens):
        if name not in REGIONS + ['全国合计']:
            continue
        length = 3 if name == '全国合计' else 4
        v = tokens[i + 1:i + 1 + length]
        if len(v) != length or not all((re.fullmatch('-?\\d+(?:\\.\\d+)?', x) for x in v)):
            continue
        if name in values:
            raise ValueError('地区数据重复')
        values[name] = (None, *map(float, v)) if name == '全国合计' else (int(v[0]), *map(float, v[1:]))
    if set(values) != set(REGIONS + ['全国合计']) or sorted((v[0] for k, v in values.items() if k != '全国合计')) != list(range(1, 32)):
        raise ValueError('地区行或增速排名不完整')
    rows = []
    for name in ['全国合计'] + REGIONS:
        if region is not None and region != name:
            continue
        rank, n2023, n2022, growth = values[name]
        for y, n in ((2022, n2022), (2023, n2023)):
            if year is None or y == year:
                rows.append({'region': name, 'year': y, 'value': n, 'growth_rank_2023': rank, 'growth_2023_percent': growth})
    return {'source': '中国民航局《2023年全国民用运输机场生产统计公报》', 'table': title, 'unit': unit, 'url': URL, 'pdf_pages': pages, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '两年数值均来自2023年公报。排名是2023年同比增速排名，并非吞吐量规模排名；增速属于2023年。旅客吞吐量为人次非独立人数，货邮为吨位。', 'rows': rows}
