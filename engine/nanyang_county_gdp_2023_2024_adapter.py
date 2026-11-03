"""《南阳统计年鉴2025》2023、2024各县区GDP。"""
import release_runtime
import hashlib
import re
import requests
URL = 'https://tj.nanyang.gov.cn/ifile/20260303/1772505075572GsaHH2fD.pdf'
REGIONS = '全市 宛城区 卧龙区 南召县 方城县 西峡县 镇平县 内乡县 淅川县 社旗县 唐河县 新野县 桐柏县 邓州市 高新区 城乡一体化示范区 官庄工区 职教园区'.split()
FIELDS = ['生产总值_万元', '第一产业_万元', '第二产业_万元', '第三产业_万元', '人均生产总值_元']

def data(year, region=None):
    if isinstance(year, bool) or year not in (2023, 2024):
        raise ValueError('仅支持2023与2024数据年份')
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要安装 PyMuPDF') from e
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks, length = ([], 0)
        for chunk in r.iter_content(65536):
            length += len(chunk)
            if length > 25000000:
                raise ValueError('PDF超过25 MB')
            chunks.append(chunk)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('来源不是 PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    found = []
    for i, p in enumerate(doc):
        text = p.get_text()
        compact = ''.join(text.split())
        if '2-9各县（市、区）生产总值（2023年）' in compact and '2-10各县（市、区）生产总值（2024年）' in compact and ('本表按当年价格计算' in compact):
            found.append((i, text))
    if len(found) != 1:
        raise ValueError('无法唯一定位官方表格')
    page_no, text = found[0]
    lines = [re.sub('\\s+', '', l) for l in text.splitlines() if l.strip()]
    rows = []
    for idx, line in enumerate(lines):
        skip = 1
        if line == '全' and idx + 1 < len(lines) and (lines[idx + 1] == '市'):
            line, skip = ('全市', 2)
        if line in REGIONS:
            values = lines[idx + skip:idx + skip + 5]
            if len(values) != 5 or not all((re.fullmatch('\\d+', v) for v in values)):
                raise ValueError(f'{line} 列解析失败')
            values = list(map(int, values))
            if abs(values[0] - sum(values[1:4])) > 3:
                raise ValueError(f'{line} 三次产业和异常')
            rows.append({'地区': line, **dict(zip(FIELDS, values))})
    if [x['地区'] for x in rows] != REGIONS * 2:
        raise ValueError('表格行数或顺序变化')
    rows = rows[(year - 2023) * len(REGIONS):(year - 2022) * len(REGIONS)]
    if region:
        rows = [r for r in rows if r['地区'] == region]
        if not rows:
            raise ValueError('地区不存在')
    return {'source': '南阳市统计局《南阳统计年鉴2025》', 'year': year, 'table': f'2-{9 + year - 2023} 各县（市、区）生产总值', 'url': URL, 'pdf_page': page_no + 1, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '按当年价格计算；万元和元，不宜直接将名义值比较视作可比价增速。开发区、工区等按原表保留，地区统计范围和口径以原表为准。', 'rows': rows}
