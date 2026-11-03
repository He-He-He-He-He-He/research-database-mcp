"""NLM DailyMed v2 drug name and structured product label access."""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
BASE = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/'

def _page(page, pagesize):
    if int(page) < 1 or not 1 <= int(pagesize) <= 100:
        raise ValueError('page 须为正整数，pagesize 为 1–100')
    return {'page': int(page), 'pagesize': int(pagesize)}

def drug_names(query, page=1, pagesize=10):
    if not query.strip():
        raise ValueError('请输入药名')
    params = {'drug_name': query, **_page(page, pagesize)}
    r = requests.get(BASE + 'drugnames.json', params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def labels(query, page=1, pagesize=10):
    if not query.strip():
        raise ValueError('请输入药名')
    params = {'drug_name': query, **_page(page, pagesize)}
    r = requests.get(BASE + 'spls.json', params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def label_sections(setid, keyword='', limit=30):
    if not re.fullmatch('[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', str(setid)):
        raise ValueError('setid 必须是 UUID')
    if not 1 <= int(limit) <= 100:
        raise ValueError('limit 为 1–100')
    u = BASE + 'spls/' + setid + '.xml'
    r = requests.get(u, timeout=35)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {'h': 'urn:hl7-org:v3'}
    out = []
    for sec in root.findall('.//h:section', ns):
        t = sec.find('h:title', ns)
        content = sec.find('h:text', ns)
        if t is None or content is None:
            continue
        title = ' '.join(' '.join(t.itertext()).split())
        text = ' '.join(' '.join(content.itertext()).split())
        if not keyword or keyword.casefold() in (title + ' ' + text).casefold():
            out.append({'title': title, 'text': text})
    return {'setid': setid, 'url': u, 'matches': len(out), 'sections': out[:int(limit)], 'note': '美国现行上市标签；并非每条都证明 FDA 批准，也非个体治疗建议。'}
