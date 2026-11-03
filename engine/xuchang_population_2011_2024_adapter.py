"""许昌统计年鉴2025各县区2011-2024常住人口。"""
import release_runtime
import hashlib, re, requests
URL = 'https://www.xuchang.gov.cn/BigFileUpLoadStorage/temp/2026-04-29/2a3644d2-953e-42af-87d2-effcd2f9b703/%E8%AE%B8%E6%98%8C%E7%BB%9F%E8%AE%A1%E5%B9%B4%E9%89%B4-2025.pdf'
REGIONS = '全市 魏都区 建安区 鄢陵县 襄城县 禹州市 长葛市'.split()

def data(year=None, region=None):
    if year is not None and (isinstance(year, bool) or year not in range(2011, 2025)):
        raise ValueError('年份须为2011—2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要 PyMuPDF') from e
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 25000000:
                raise ValueError('PDF超限')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    d = fitz.open(stream=raw, filetype='pdf')
    s = d[87].get_text()
    compact = ''.join(s.split())
    if '3-3各县（市、区）年末常住人口' not in compact or '单位：万人' not in compact:
        raise ValueError('未找到预期表')
    lines = [''.join(x.split()) for x in s.splitlines() if x.strip()]
    rows = []
    years = []
    for i, x in enumerate(lines):
        if re.fullmatch('20(?:1[1-9]|2[0-4])', x):
            v = lines[i + 1:i + 8]
            if len(v) != 7 or not all((re.fullmatch('\\d+\\.\\d+', a) for a in v)):
                raise ValueError('人口数值列异常')
            y = int(x)
            years.append(y)
            for name, value in zip(REGIONS, v):
                if (year is None or year == y) and (region is None or region == name):
                    rows.append({'地区': name, '年份': y, '常住人口_万人': float(value)})
    if years != list(range(2011, 2025)):
        raise ValueError('年份列表不完整或重复')
    return {'source': '许昌市统计局《许昌统计年鉴2025》', 'table': '3-3 各县（市、区）年末常住人口', 'url': URL, 'pdf_page': 88, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '依据2020年第七次全国人口普查结果，对2011年以来的常住人口和城镇化率进行了修订；四舍五入可能导致总计与分项之和不等。仅原表6县市区和全市。', 'rows': rows}
