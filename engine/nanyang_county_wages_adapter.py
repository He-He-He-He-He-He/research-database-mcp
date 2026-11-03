"""南阳统计年鉴重点年份城镇非私营单位在岗职工平均工资。"""
import release_runtime
import hashlib
import requests
URL = 'https://tj.nanyang.gov.cn/ifile/20260303/1772505075572GsaHH2fD.pdf'
YEARS = (1978, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2014, 2015, 2016, 2017, 2018, 2019)
REGIONS = '全市 合计 宛城区 卧龙区 南召县 方城县 西峡县 镇平县 内乡县 淅川县 社旗县 唐河县 新野县 桐柏县 邓州市 高新区 城乡一体化示范区 官庄工区 职教园区'.split()

def data(year=None, region=None):
    if year is not None and (isinstance(year, bool) or year not in YEARS):
        raise ValueError('不支持该年份')
    if region is not None and region not in REGIONS:
        raise ValueError('地区不存在')
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('需要 PyMuPDF') from exc
    with requests.get(URL, timeout=60, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 25000000:
                raise ValueError('PDF超过大小限制')
            chunks.append(b)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('未获得PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    page = doc[135]
    title = '4-7各县（市、区）重点年份城镇非私营单位在岗职工平均工资'
    if title not in ''.join(page.get_text().split()):
        raise ValueError('原表位置已变化')
    words = page.get_text('words')
    out = []
    for y0, y1, years in [(150, 450, YEARS[:8]), (520, 790, YEARS[8:])]:
        ws = [w for w in words if y0 <= w[1] < y1]
        headers = {int(w[4]): (w[0] + w[2]) / 2 for w in ws if w[4].isdigit() and int(w[4]) in years and (w[1] < y0 + 15)}
        if set(headers) != set(years):
            raise ValueError('表头年份无法验证')
        labelwords = [w for w in ws if w[0] < 160 and w[1] > y0 + 15 and (not w[4].isdigit())]
        groups = []
        for w in sorted(labelwords, key=lambda a: (a[1], a[0])):
            if groups and abs(w[1] - groups[-1][0]) < 3:
                groups[-1][1].append(w)
            else:
                groups.append([w[1], [w]])
        regionrows = []
        for yy, ww in groups:
            name = ''.join((w[4] for w in sorted(ww, key=lambda x: x[0])))
            if name not in REGIONS:
                continue
            nums = [w for w in ws if w[0] >= 160 and abs(w[1] - yy) < 3 and w[4].isdigit()]
            values = {}
            for w in nums:
                x = (w[0] + w[2]) / 2
                nearest = min(headers, key=lambda v: abs(headers[v] - x))
                if abs(headers[nearest] - x) > 22 or nearest in values:
                    raise ValueError('列坐标无法唯一归属')
                values[nearest] = int(w[4])
            regionrows.append(name)
            for yr in years:
                if (year is None or year == yr) and (region is None or region == name):
                    out.append({'地区': name, '年份': yr, '在岗职工平均工资_元': values.get(yr)})
        if regionrows != REGIONS:
            raise ValueError('地区数量或顺序异常')
    return {'source': '南阳市统计局《南阳统计年鉴2025》', 'table': title, 'url': URL, 'pdf_page': 136, 'sha256': hashlib.sha256(raw).hexdigest(), 'note': '单位元；仅涵盖城镇非私营单位在岗职工，不能等同全体就业人员。合计不含邓州市。原表空白保留为 null，非零值。重点年份不连续。', 'rows': out}
