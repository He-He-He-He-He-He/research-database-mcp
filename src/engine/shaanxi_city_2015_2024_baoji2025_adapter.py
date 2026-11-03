"""宝鸡统计年鉴2025转引陕西各市区主要指标。"""
import release_runtime
import hashlib
import re
import requests
URL = 'https://tjj.baoji.gov.cn/col1925/col18051/202604/P020260429564143619173.pdf'
REGIONS = '西安市 铜川市 宝鸡市 咸阳市 渭南市 延安市 汉中市 榆林市 安康市 商洛市 杨凌示范区'.split()
METRICS = {'gdp_growth': (40, 0, '生产总值比上年增长速度', '%', 2), 'gdp': (40, 1, '生产总值', '亿元', 2), 'gdp_per_capita': (41, 0, '人均生产总值', '元', 2), 'local_revenue': (42, 0, '地方财政收入', '亿元', 1), 'retail': (43, 0, '社会消费品零售总额', '亿元', 2), 'urban_income': (43, 1, '城镇居民人均可支配收入', '元', 2), 'population': (44, 0, '年末常住人口', '万人', 2), 'rural_income': (44, 1, '农民人均可支配收入', '元', 2)}

def data(metric, year=None, region=None):
    if metric not in METRICS:
        raise ValueError('指标仅支持 ' + ', '.join(METRICS))
    if year is not None and (isinstance(year, bool) or year not in range(2015, 2025)):
        raise ValueError('年份须为 2015—2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装 PyMuPDF') from e
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 20000000:
                raise ValueError('PDF过大')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('未获得PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    page_no, group, title, unit, count = METRICS[metric]
    text = doc[page_no - 1].get_text()
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if title not in ''.join(lines) or any((r not in lines for r in REGIONS)):
        raise ValueError('表题或地区表头异常')
    records = []
    for i, line in enumerate(lines):
        if re.fullmatch('20(?:1[5-9]|2[0-4])', line) and i + 12 < len(lines) and (lines[i + 1] == line + '年'):
            vals = lines[i + 2:i + 13]
            if all((re.fullmatch('-?\\d+(?:\\.\\d+)?', v) for v in vals)):
                records.append((int(line), vals))
    if [y for y, _ in records] != list(range(2015, 2025)) * count:
        raise ValueError('年份行数量或顺序异常')
    rows = []
    for y, values in records[group * 10:(group + 1) * 10]:
        for r, v in zip(REGIONS, values):
            if (year is None or year == y) and (region is None or region == r):
                rows.append({'year': y, 'region': r, 'value': float(v)})
    return {'source': '宝鸡市统计局《宝鸡统计年鉴2025》', 'table': f'全省各市（区）{title}', 'unit': unit, 'source_url': URL, 'pdf_page': page_no, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '包括陕西10个地级市及杨凌示范区；数据为宝鸡年鉴汇编，杨凌为示范区非地级市。生产总值增长速度按可比价格计算；不同版次存在修订可能，跨年比较应核原表口径。', 'rows': rows}
