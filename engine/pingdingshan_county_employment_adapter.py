"""《平顶山年鉴2024》县区全社会就业人员历史数据。"""
import release_runtime
import hashlib
import re
import requests
URL = 'https://tjj.pds.gov.cn/upload/files/2025/4/%E5%B9%B3%E9%A1%B6%E5%B1%B1%E5%B9%B4%E9%89%B4%EF%BC%882024%EF%BC%89.pdf'
REGIONS = '全市 新华区 卫东区 石龙区 湛河区 高新区 示范区 宝丰县 叶县 鲁山县 郏县 舞钢市 汝州市'.split()

def data(year=None, region=None):
    years = list(range(2010, 2024))
    if year is not None and (isinstance(year, bool) or year not in years):
        raise ValueError('年份须为2010—2023')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装 PyMuPDF') from e
    with requests.get(URL, timeout=90, stream=True) as r:
        r.raise_for_status()
        size = 0
        chunks = []
        for b in r.iter_content(65536):
            size += len(b)
            if size > 70000000:
                raise ValueError('PDF超过70 MB')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('未获得官方PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    p = doc[143]
    text = p.get_text()
    if '4-2历年各县（市、区）全社会就业人员数' not in ''.join(text.split()) or '2010-2020年就业人员' not in ''.join(text.split()):
        raise ValueError('原表结构或位置发生变化')
    words = p.get_text('words')
    h = [w for w in words if '2010年2011年2012年' in w[4]]
    if len(h) != 1 or h[0][4] != ''.join((str(y) + '年' for y in years)):
        raise ValueError('年份表头异常')
    labels = [w for w in words if w[0] < 115 and 165 < w[1] < 410 and re.fullmatch('[\\u4e00-\\u9fff]+', w[4])]
    grouped = []
    for w in sorted(labels, key=lambda w: (w[1], w[0])):
        if grouped and abs(w[1] - grouped[-1][0]) < 3:
            grouped[-1][1].append(w)
        else:
            grouped.append([w[1], [w]])
    names = [''.join((w[4] for w in sorted(g, key=lambda w: w[0]))) for _, g in grouped]
    if names != REGIONS:
        raise ValueError('地区行或顺序异常')
    first_y = grouped[0][0]
    first = sorted([w for w in words if w[0] > 115 and abs(w[1] - first_y) < 3 and re.fullmatch('\\d+\\.\\d+', w[4])], key=lambda w: w[0])
    if len(first) != len(years):
        raise ValueError('全市年份列异常')
    xs = [(w[0] + w[2]) / 2 for w in first]
    rows = []
    for (yy, _), name in zip(grouped, names):
        vals = {}
        for w in words:
            if w[0] <= 115 or abs(w[1] - yy) >= 3 or (not re.fullmatch('\\d+\\.\\d+', w[4])):
                continue
            x = (w[0] + w[2]) / 2
            j = min(range(len(xs)), key=lambda i: abs(xs[i] - x))
            if abs(xs[j] - x) > 12 or j in vals:
                raise ValueError('数字列归属异常')
            vals[j] = float(w[4])
        for j, y in enumerate(years):
            if (region is None or name == region) and (year is None or year == y):
                rows.append({'地区': name, '年份': y, '全社会就业人员_万人': vals.get(j)})
    return {'source': '平顶山市统计局发布《平顶山年鉴2024》', 'table': '4-2 历年各县（市、区）全社会就业人员数', 'source_url': URL, 'pdf_page': 144, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '原注：2010—2020年就业人员按照2010年、2020年人口普查数据和劳动力调查数据修订。原表空白为 null；高新区、示范区为功能区，非全部均为县级行政区。', 'rows': rows}
