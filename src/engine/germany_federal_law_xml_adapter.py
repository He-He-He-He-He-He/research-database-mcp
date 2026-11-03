"""Germany Federal Office of Justice daily federal law XML catalogue and provision."""
import release_runtime
import io, re, zipfile
import xml.etree.ElementTree as ET
import requests
BASE = 'https://www.gesetze-im-internet.de'
INDEX = BASE + '/gii-toc.xml'

def _get(url, max_bytes):
    with requests.get(url, timeout=40, stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError('Source too large')
            chunks.append(chunk)
        return b''.join(chunks)

def search(keyword, limit=10, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must be 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50) or (type(offset) is not int) or (offset < 0):
        raise ValueError('limit must be 1–50 and offset nonnegative')
    root = ET.fromstring(_get(INDEX, 5000000))
    if root.tag != 'items':
        raise ValueError('Unexpected catalogue structure')
    rows = []
    for item in root.findall('item'):
        title = item.findtext('title', '')
        link = item.findtext('link', '')
        if keyword.casefold() not in title.casefold():
            continue
        match = re.fullmatch('http://www\\.gesetze-im-internet\\.de/([a-z0-9_-]+)/xml\\.zip', link)
        if not match:
            raise ValueError('Unexpected catalogue link')
        rows.append({'title': title, 'slug': match.group(1), 'xml_zip_url': BASE + '/' + match.group(1) + '/xml.zip', 'original_catalogue_url': link})
    return {'source_url': INDEX, 'total_matching': len(rows), 'offset': offset, 'returned': len(rows[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(rows) else None, 'truncated': offset + limit < len(rows), 'items': rows[offset:offset + limit], 'note': 'Daily catalogue. German federal consolidated text is unofficial; not case law or commentary. The catalogue is refetched each time and source updates may change order.'}

def provision(slug, number):
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9_-]{1,100}', slug):
        raise ValueError('Invalid law slug')
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 9999):
        raise ValueError('Provision number must be 1–9999')
    catalogue = ET.fromstring(_get(INDEX, 5000000))
    matching = [x for x in catalogue.findall('item') if x.findtext('link', '') == 'http://www.gesetze-im-internet.de/' + slug + '/xml.zip']
    if len(matching) != 1:
        raise ValueError('Law slug is not unique in official catalogue')
    url = BASE + '/' + slug + '/xml.zip'
    raw = _get(url, 5000000)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = [i for i in z.infolist() if not i.is_dir() and i.filename.endswith('.xml')]
        if len(entries) != 1 or entries[0].file_size > 30000000:
            raise ValueError('Unexpected XML archive')
        root = ET.fromstring(z.read(entries[0]))
    rows = []
    for n in root.findall('norm'):
        m = n.find('metadaten')
        if m is None or m.findtext('enbez') != f'§ {number}':
            continue
        content = n.find('textdaten/text/Content')
        rows.append({'label': m.findtext('enbez'), 'title': m.findtext('titel'), 'text': ' '.join(' '.join(content.itertext()).split()) if content is not None else None})
    return {'source_url': url, 'catalogue_title': matching[0].findtext('title'), 'builddate': root.get('builddate'), 'items': rows, 'note': 'Unofficial consolidated German federal law; check official Bundesgesetzblatt and amendment dates. Scope excludes commentaries and case law.'}
