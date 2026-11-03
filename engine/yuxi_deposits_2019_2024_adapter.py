"""玉溪统计年鉴2024表10-13，住户存款原表。"""
import release_runtime
import hashlib, re, requests
URL = 'https://m.yuxi.gov.cn/u/cms/yxszfxxgk/202601/05181012stvh.pdf'
REGIONS = '合计 红塔区 江川区 通海县 华宁县 易门县 峨山县 新平县 元江县 澄江市'.split()

def data(year=None, region=None):
    if year is not None and (isinstance(year, bool) or year not in range(2019, 2025)):
        raise ValueError('支持2019—2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要 PyMuPDF') from e
    with requests.get(URL, timeout=50, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 20000000:
                raise ValueError('PDF超限')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    d = fitz.open(stream=raw, filetype='pdf')
    text = d[244].get_text()
    s = ''.join(text.split())
    if '10-13住户存款' not in s or '2019年2020年2021年2022年2023年2024年' not in s:
        raise ValueError('表题或年份异常')
    lines = [''.join(x.split()) for x in text.splitlines() if x.strip()]
    i = next((i for i, x in enumerate(lines) if x.startswith('10-13住户存款')))
    lines = lines[i + 1:]
    parsed = []
    for i, name in enumerate(lines):
        if name not in REGIONS:
            continue
        v = []
        for x in lines[i + 1:]:
            if x in REGIONS:
                break
            if not re.fullmatch('\\d+(?:\\.\\d+)?', x):
                break
            v.append(x)
        if name == '合计':
            if len(v) != 14 or any((v[j] != v[j + 1] for j in range(0, 14, 2))):
                raise ValueError('合计重复层异常')
            v = v[::2]
        if len(v) != 7:
            raise ValueError(f'{name}数据列异常')
        parsed.append((name, v))
    if [x[0] for x in parsed] != REGIONS:
        raise ValueError('地区数或顺序异常')
    rows = []
    for name, v in parsed:
        if region and region != name:
            continue
        for y, value in zip(range(2019, 2025), v[:6]):
            if year is None or year == y:
                rows.append({'地区': name, '年份': y, '住户存款_万元': int(value), '2024比上年增长_百分比': float(v[6])})
    return {'source': '玉溪市统计局、国家统计局玉溪调查队《玉溪统计年鉴2024》', 'table': '10-13 住户存款', 'url': URL, 'pdf_page': 245, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '原年鉴名为2024且明确收录2024年数据。原表总计PDF文本有双层重复字，必须逐对验证后去重；增长率均为2024比2023，不是各年份增速。', 'rows': rows}
