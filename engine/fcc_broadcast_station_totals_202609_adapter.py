"""FCC 2026-09-30 broadcast station totals, official DA 26-1064 notice."""
import release_runtime
import re
import requests
URL = 'https://docs.fcc.gov/public/attachments/DA-26-1064A1.txt'
LABELS = ['AM STATIONS', 'FM COMMERCIAL', 'FM EDUCATIONAL', 'TOTAL', 'UHF COMMERCIAL TV', 'VHF COMMERCIAL TV', 'UHF EDUCATIONAL TV', 'VHF EDUCATIONAL TV', 'TOTAL', 'CLASS A UHF STATIONS', 'CLASS A VHF STATIONS', 'TOTAL', 'FM TRANSLATORS & BOOSTERS', 'UHF TRANSLATORS', 'VHF TRANSLATORS', 'TOTAL', 'UHF LOW POWER TV', 'VHF LOW POWER TV', 'TOTAL', 'LOW POWER FM', 'TOTAL', 'TOTAL BROADCAST STATIONS']

def _parse(text):
    if 'BROADCAST STATION TOTALS AS OF SEPTEMBER 30, 2026' not in text.upper():
        raise ValueError('unexpected FCC notice')
    body = text[text.upper().index('THE COMMISSION HAS ANNOUNCED'):]
    lines = [x.strip() for x in body.replace('\r', '\n').splitlines() if x.strip()]
    rows = []
    pos = 0
    for label in LABELS:
        while pos < len(lines) and lines[pos].upper() != label:
            pos += 1
        if pos >= len(lines):
            raise ValueError('FCC label missing: ' + label)
        pos += 1
        if pos >= len(lines) or not re.fullmatch('[0-9][0-9,]*', lines[pos]):
            raise ValueError('FCC value missing: ' + label)
        rows.append({'label': label, 'count': int(lines[pos].replace(',', '')), 'raw_count': lines[pos]})
        pos += 1
    return rows

def totals():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    r.encoding = 'utf-8-sig'
    return {'source': URL, 'notice': 'DA 26-1064', 'released': '2026-10-06', 'as_of': '2026-09-30', 'rows': _parse(r.text), 'note': 'FCC licensed station totals at one historical snapshot, not audience, viewership, number of operators, or global stations. Repeated TOTAL rows are subtotals in source order and overlap component categories; do not sum totals and components. Translator/booster counts are not independent full-power broadcasters.'}
