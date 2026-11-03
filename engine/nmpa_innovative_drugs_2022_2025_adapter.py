"""NMPA 2022–2025 innovative-drug approval table from annual reports."""
import release_runtime
import re
import requests, fitz
from nmpa_drug_approvals_2022_2025_adapter import SOURCES

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
    if len(d) < 6:
        raise ValueError('unexpected PDF length')
    text = d[5].get_text()
    m = re.search('表\\s*5\\s*批准创新药上市、临床试验情况(.*?)表\\s*6', text, re.S)
    if not m:
        raise ValueError('table 5 not found on physical page 6')
    section = m.group(1)
    normal = re.sub('\\s+', '', section)
    if f'{year}年' not in normal or '批准上市品种数量' not in normal or '批准临床品种数量' not in normal:
        raise ValueError('year or headers mismatch')
    units = re.search('单位：([^项]+?)项', normal)
    if not units or units.group(1) not in ('个', '个、件'):
        raise ValueError('unexpected units')
    rows = []
    for label in ('中药天然药物', '化学药品', '生物制品', '合计'):
        p = '合\\s*计' if label == '合计' else re.escape(label)
        matched = list(re.finditer(p + '\\s+(\\d+)\\s+(\\d+)\\b', section))
        if len(matched) != 1:
            raise ValueError('unexpected row structure')
        rows.append({'category': label, 'approved_marketing': int(matched[0].group(1)), 'approved_clinical': int(matched[0].group(2))})
    for key in ('approved_marketing', 'approved_clinical'):
        if sum((v[key] for v in rows[:3])) != rows[-1][key]:
            raise ValueError('category total mismatch')
    return {'source': '国家药品监督管理局综合和规划财务司、信息中心', 'year': year, 'pdf_url': SOURCES[year], 'physical_page': 6, 'source_unit': units.group(1), 'rows': rows, 'source_table_text': m.group(0), 'note': '创新药品种审批数量；2022表头单位为个，后续表头为个、件，跨年比较需复核原报告口径。'}
