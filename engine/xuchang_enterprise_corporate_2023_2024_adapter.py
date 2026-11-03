"""许昌各县（市、区）企业法人单位数，官方2025统计年鉴。"""
import release_runtime
import hashlib
import requests
URL = 'https://www.xuchang.gov.cn/BigFileUpLoadStorage/temp/2026-04-29/2a3644d2-953e-42af-87d2-effcd2f9b703/%E8%AE%B8%E6%98%8C%E7%BB%9F%E8%AE%A1%E5%B9%B4%E9%89%B4-2025.pdf'
REGIONS = '全市 魏都区 建安区 鄢陵县 襄城县 开发区 禹州市 长葛市 东城区 示范区'.split()

def data(year, region=None):
    if isinstance(year, bool) or year not in (2023, 2024):
        raise ValueError('仅提供2023、2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装 PyMuPDF') from e
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        size = 0
        chunks = []
        for b in r.iter_content(65536):
            size += len(b)
            if size > 25000000:
                raise ValueError('PDF过大')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('未返回PDF')
    d = fitz.open(stream=raw, filetype='pdf')
    p = d[65]
    compact = ''.join(p.get_text().split())
    if not all((f'1-{10 + i}各县(市、区)按登记注册类型分企业法人单位数({2023 + i}年)' in compact for i in range(2))):
        raise ValueError('原表位置或标题已改变')
    ws = p.get_text('words')
    heading_y, total_y = (130, 168) if year == 2023 else (523, 561)
    headings = sorted([w for w in ws if abs(w[1] - heading_y) < 2 and w[0] > 160], key=lambda w: w[0])
    texts = [w[4] for w in headings]
    if texts != ['全', '市'] + REGIONS[1:]:
        raise ValueError('地区表头变化')
    nums = sorted([w for w in ws if abs(w[1] - total_y) < 2 and w[0] > 160 and w[4].isdigit()], key=lambda w: w[0])
    if len(nums) != len(REGIONS):
        raise ValueError('合计行数据列数异常')
    vals = list(map(lambda w: int(w[4]), nums))
    if vals[0] != sum(vals[1:]):
        raise ValueError('全市与分地区之和不一致')
    rows = [{'地区': a, '企业法人单位数_个': b} for a, b in zip(REGIONS, vals) if region is None or region == a]
    return {'source': '许昌市统计局《许昌统计年鉴2025》', 'data_year': year, 'table': f'1-{10 + year - 2023} 各县（市、区）按登记注册类型分企业法人单位数（合计行）', 'url': URL, 'pdf_page': 66, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '仅提取合计行；不含各登记注册类别细分；开发区、东城区、示范区为原表地区，不等同县级行政区；原表全市口径以原年鉴为准。', 'rows': rows}
