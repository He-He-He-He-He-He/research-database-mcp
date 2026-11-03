"""Selected NMPA annual new drug application approval tables, 2022–2025."""
import release_runtime
import re
import requests, fitz
SOURCES = {2022: 'https://www.nmpa.gov.cn/directory/web/nmpa/images/1681866563446076174.pdf', 2023: 'https://www.nmpaic.org.cn/yjzxyw/202505/P020250516549271920003.pdf', 2024: 'https://www.nmpa.gov.cn/directory/web/nmpa/images/1755850263549015691.pdf', 2025: 'https://www.nmpaic.org.cn/yjzxyw/202609/P020260907517838255969.pdf'}

def catalog():
    return [{'year': y, 'pdf_url': u} for y, u in sorted(SOURCES.items(), reverse=True)]

def report(year):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('supported years: 2022–2025')
    with requests.get(SOURCES[year], timeout=(10, 50), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('file exceeds limit')
    if not raw.startswith(b'%PDF-'):
        raise ValueError('not a PDF')
    d = fitz.open(stream=bytes(raw), filetype='pdf')
    if len(d) < 5:
        raise ValueError('unexpected PDF length')
    text = d[4].get_text()
    m2 = re.search('表\\s*2\\s*境内新药临床申请申报的审批情况(.*?)表\\s*3', text, re.S)
    m3 = re.search('表\\s*3\\s*新上市药品的申报审批情况(.*?)表\\s*4', text, re.S)
    if not m2 or not m3:
        raise ValueError('expected table boundaries not found on physical page 5')

    def parse(section, kind):
        if not re.search(f'{year}\\s*年', section) or '单位：件' not in re.sub('\\s+', '', section):
            raise ValueError('wrong year or unit')
        rows = []
        for label in ('中药天然药物', '化学药品', '生物制品'):
            ms = list(re.finditer(re.escape(label) + '\\s+(\\d+)\\b', section))
            if len(ms) != 1:
                raise ValueError('unexpected row structure')
            rows.append({'category': label, 'value': int(ms[0].group(1)), 'unit': '件'})
        if kind == 'clinical':
            totals = list(re.finditer('合\\s*计\\s+(\\d+)\\b', section))
            if len(totals) != 1 or sum((x['value'] for x in rows)) != int(totals[0].group(1)):
                raise ValueError('clinical table total mismatch')
            rows.append({'category': '合计', 'value': int(totals[0].group(1)), 'unit': '件'})
        return rows
    return {'source': '国家药品监督管理局综合和规划财务司、信息中心', 'year': year, 'pdf_url': SOURCES[year], 'physical_page': 5, 'clinical_trial_approvals': parse(m2.group(1), 'clinical'), 'new_market_approvals': parse(m3.group(1), 'market'), 'source_text': text, 'note': '仅表2境内新药临床申请和表3新上市药品审批数量，单位为申请件；不是药品品种数、销量或临床结果。'}
