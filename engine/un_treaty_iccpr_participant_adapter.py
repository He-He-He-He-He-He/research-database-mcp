"""UN Treaty Collection ICCPR participant table, preserving footnote references."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://treaties.un.org/Pages/ViewDetails.aspx'
PARAMS = {'chapter': '4', 'mtdsg_no': 'IV-4', 'src': 'IND'}

def participant(name):
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError('name must be 1–100 characters')
    with requests.get(URL, params=PARAMS, timeout=50, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 10000000:
                raise ValueError('Source page too large')
            chunks.append(chunk)
        source_url = r.url
    soup = BeautifulSoup(b''.join(chunks), 'html.parser')
    text = soup.get_text(' ', strip=True)
    stamp = re.search('STATUS AS AT\\s*:\\s*(\\d{2}-\\d{2}-\\d{4}\\s+\\d{2}:\\d{2}:\\d{2}\\s+\\w+)', text)
    if not stamp or 'International Covenant on Civil and Political Rights' not in text:
        raise ValueError('Unexpected treaty page')
    candidates = []
    for t in soup.find_all('table'):
        first = t.find('tr')
        if first:
            headers = [' '.join(x.get_text(' ', strip=True).split()) for x in first.find_all(['td', 'th'], recursive=False)]
            if len(headers) == 3 and headers[0] == 'Participant' and (headers[1] == 'Signature') and ('Accession' in headers[2]):
                candidates.append(t)
    if not candidates:
        raise ValueError('Participant table not found')
    table = candidates[-1]
    rows = []
    for tr in table.find_all('tr')[1:]:
        cells = tr.find_all('td', recursive=False)
        if len(cells) != 3:
            continue
        first = BeautifulSoup(str(cells[0]), 'html.parser')
        notes = [x.get_text(' ', strip=True) for x in first.select('sup a')]
        for x in first.select('sup'):
            x.decompose()
        country = ' '.join(first.get_text(' ', strip=True).split())
        if country.casefold() == name.strip().casefold():
            rows.append({'participant': country, 'footnote_numbers': notes, 'signature_raw': ' '.join(cells[1].get_text(' ', strip=True).split()) or None, 'accession_succession_ratification_raw': ' '.join(cells[2].get_text(' ', strip=True).split()) or None})
    return {'source_url': source_url, 'treaty': 'International Covenant on Civil and Political Rights (IV-4)', 'status_as_at': stamp.group(1), 'items': rows, 'note': 'Raw participant table only; read official footnotes, reservations and declarations. Empty entry does not by itself determine treaty status or territorial effect.'}
