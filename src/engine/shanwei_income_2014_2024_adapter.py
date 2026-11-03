"""汕尾2025年鉴各县区2014-24居民人均收入。"""
import release_runtime
import hashlib, re, requests
URL = 'https://www.shanwei.gov.cn/attachment/0/83/83058/1232150.pdf'
REGIONS = '全市 市城区 海丰县 陆丰市 陆河县'.split()
KINDS = {'all': ('11-8', '全体常住居民', 285), 'urban': ('11-9', '城镇常住居民', 285), 'rural': ('11-10', '农村常住居民', 286)}

def data(kind, year=None, region=None):
    if kind not in KINDS:
        raise ValueError('kind须为all、urban或rural')
    if year is not None and (isinstance(year, bool) or year not in range(2014, 2025)):
        raise ValueError('年份须为2014–2024')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装PyMuPDF') from e
    with requests.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 15000000:
                raise ValueError('PDF超限')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    d = fitz.open(stream=raw, filetype='pdf')
    tab, label, page = KINDS[kind]
    s = d[page - 1].get_text()
    title = f'{tab}各县（市、区）{label}人均可支配收入'
    if title not in ''.join(s.split()):
        raise ValueError('表题或位置变化')
    lines = [re.sub('\\s+', ' ', line).strip() for line in s.splitlines() if line.strip()]
    pos = next((i for i, l in enumerate(lines) if ''.join(l.split()).startswith(title)))
    part = []
    for l in lines[pos + 1:]:
        if re.match('^11-\\d+', l) or l.startswith('注：'):
            break
        part.append(l)
    rows = []
    for i, l in enumerate(part):
        name = ''.join(l.split())
        if name not in REGIONS:
            continue
        data_lines = []
        for x in part[i + 1:]:
            if ''.join(x.split()) in REGIONS:
                break
            data_lines.extend(x.split())
        if len(data_lines) != 11 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', x) for x in data_lines)):
            raise ValueError(f'{name}年份列异常')
        for y, v in zip(range(2014, 2025), data_lines):
            if (year is None or year == y) and (region is None or region == name):
                rows.append({'地区': name, '年份': y, '人均可支配收入_元': float(v)})
    seen = [''.join(l.split()) for l in part if ''.join(l.split()) in REGIONS]
    if seen != REGIONS:
        raise ValueError('地区次序变化')
    return {'source': '汕尾市统计局《汕尾统计年鉴2025》', 'table': title, 'url': URL, 'pdf_page': page, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '覆盖全市、市城区、海丰县、陆丰市、陆河县；分全体、城镇、农村常住居民。原注称城乡一体化调查2014年起发布；农村2014年以前纯收入不完全可比。', 'rows': rows}
