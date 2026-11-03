"""济南统计年鉴2025，2023与2024分地区规上服务业财务数据。"""
import release_runtime
import hashlib, re
import requests
URL = 'https://jntj.jinan.gov.cn/cms_files/complat3/1631/attach/20261/b26d31899922425091afba6bb0bc4a99.pdf'
REGIONS = '总计 历下区 市中区 槐荫区 天桥区 历城区 长清区 章丘区 济阳区 莱芜区 钢城区 济南高新区 济南起步区（直管） 南部山区 平阴县 商河县'.split()
FIELDS = ['企业单位数_个', '资产总计_万元', '负债合计_万元', '营业收入_万元', '营业成本_万元']

def data(year, region=None):
    if isinstance(year, bool) or year not in (2023, 2024):
        raise ValueError('仅支持2023或2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要 PyMuPDF') from e
    with requests.get(URL, timeout=70, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 30000000:
                raise ValueError('PDF超出限制')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('返回内容不是PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    page = 319 if year == 2023 else 327
    p = doc[page - 1]
    text = p.get_text()
    title = f'14-{(4 if year == 2023 else 8)}规模以上服务业企业分地区主要财务指标（{year}年）'
    if title not in ''.join(text.split()):
        raise ValueError('原表标题或位置已改变')
    lines = [re.sub('\\s+', '', x) for x in text.splitlines() if x.strip()]
    rows = []
    for i, name in enumerate(lines):
        if name not in REGIONS:
            continue
        v = lines[i + 2:i + 7]
        if len(v) != 5 or not all((re.fullmatch('\\d+', n) for n in v)):
            raise ValueError(f'{name}数据列异常')
        rows.append({'地区': name, **dict(zip(FIELDS, map(int, v)))})
    if [r['地区'] for r in rows] != REGIONS:
        raise ValueError('地区名称或顺序变化')
    if rows[0][FIELDS[0]] != sum((r[FIELDS[0]] for r in rows[1:])):
        raise ValueError('企业数量合计异常')
    if region:
        rows = [r for r in rows if r['地区'] == region]
    return {'source': '济南市统计局《济南统计年鉴2025》', 'year': year, 'table': title, 'source_url': URL, 'pdf_page': page, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '仅原表首页五列；企业个数以个计，其余为万元，不含续页指标。规模以上服务业统计口径以原年鉴为准，功能区按原表列出，不能视为全部独立行政区。', 'rows': rows}
