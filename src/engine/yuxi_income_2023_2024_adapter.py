"""玉溪统计年鉴2024：2023/2024市县人均收入和消费。"""
import release_runtime
import hashlib, re, requests
URL = 'https://m.yuxi.gov.cn/u/cms/yxszfxxgk/202601/05181012stvh.pdf'
REGIONS = '玉溪市 红塔区 江川区 通海县 华宁县 易门县 峨山县 新平县 元江县 澄江市'.split()
KINDS = {'all': ('10-10', '全体居民', 244), 'urban': ('10-11', '城镇常住居民', 244), 'rural': ('10-12', '农村常住居民', 245)}

def data(kind, year=None, region=None):
    if kind not in KINDS:
        raise ValueError('kind须为all、urban或rural')
    if year is not None and (isinstance(year, bool) or year not in (2023, 2024)):
        raise ValueError('仅支持2023或2024')
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
                raise ValueError('PDF超过限制')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('PDF异常')
    doc = fitz.open(stream=raw, filetype='pdf')
    tab, label, page = KINDS[kind]
    text = doc[page - 1].get_text()
    prefix = f'{tab}各县（市、区）{label}人均可支配收入和人均生活消费支出'
    compact = ''.join(text.split())
    if prefix not in compact:
        raise ValueError('表题异常')
    lines = [re.sub('\\s+', '', x) for x in text.splitlines() if x.strip()]
    pos = next((i for i, l in enumerate(lines) if l.startswith(tab + '各县')))
    chunk = []
    for l in lines[pos + 1:]:
        if re.match('^10-\\d+', l):
            break
        chunk.append(l)
    result = []
    for i, name in enumerate(chunk):
        if name not in REGIONS:
            continue
        v = chunk[i + 1:i + 7]
        if len(v) != 6 or not all((re.fullmatch('\\d+(?:\\.\\d+)?', x) for x in v)):
            raise ValueError(f'{name}数据不完整')
        result.append((name, list(map(float, v))))
    if [x[0] for x in result] != REGIONS:
        raise ValueError('地区数或顺序异常')
    rows = []
    for name, v in result:
        if region and name != region:
            continue
        for y, income, spend in [(2023, v[0], v[3]), (2024, v[1], v[4])]:
            if year is None or year == y:
                rows.append({'地区': name, '年份': y, '人均可支配收入_元': income, '人均生活消费支出_元': spend, '2024收入比2023增长_百分比': v[2], '2024消费比2023增长_百分比': v[5]})
    return {'source': '玉溪市统计局、国家统计局玉溪调查队《玉溪统计年鉴2024》', 'table': prefix, 'url': URL, 'pdf_page': page, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '版名为2024但编者说明明确收录2024年度数据；各行2024年增速随2023/2024记录重复返回，请勿误认为2023增速；分全体、城镇、农村，按原表口径。', 'rows': rows}
