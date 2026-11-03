"""EBRD official bulk CSV projects, not a vendor-provided query API."""
import release_runtime
import csv, io, re, requests
PAGE = 'https://www.ebrd.com/home/what-we-do/projects.html'
URL = 'https://www.ebrd.com/content/dam/ebrd_dxp/projectsData.csv'
FIELDS = ['Publication date', 'Project ID', 'Country', 'Title', 'Sector', 'Project type', 'Notice Type', 'ESIA available', 'Project status', 'Approval Date', 'Environmental Category', 'EBRD Finance Summary', 'Total Project cost', 'PSD Last Updated date', 'URL link to project']

def search(country='', keyword='', status='', offset=0, limit=20):
    for v in (country, keyword, status):
        if not isinstance(v, str) or len(v) > 150:
            raise ValueError('Invalid text filter')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    with requests.get(URL, stream=True, timeout=(15, 40)) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 8000000:
                raise RuntimeError('EBRD project CSV exceeds 8 MB')
            parts.append(b)
    reader = csv.DictReader(io.StringIO(b''.join(parts).decode('utf-8-sig'), newline=''))
    if reader.fieldnames != FIELDS:
        raise RuntimeError('Unexpected EBRD project CSV fields')
    out = []
    count = 0
    total = 0
    for row in reader:
        if None in row or set(row) != set(FIELDS):
            raise RuntimeError('Malformed EBRD project CSV row')
        total += 1
        if country and row['Country'].casefold() != country.strip().casefold():
            continue
        if keyword and keyword.casefold() not in row['Title'].casefold():
            continue
        if status and row['Project status'].casefold() != status.strip().casefold():
            continue
        if offset <= count < offset + limit:
            out.append(row)
        count += 1
    return {'source': 'European Bank for Reconstruction and Development (EBRD)', 'source_page': PAGE, 'download_url': URL, 'source_type': 'official bulk CSV, local filtering; not an EBRD query API', 'count_all': total, 'matched': count, 'offset': offset, 'items': out, 'note': 'Country and status filters are exact; title keyword is a substring. All fields, dates, currencies, blanks and amounts remain verbatim. EBRD finance and total project cost are different measures and may overlap. Project status governs interpretation: future approval dates can be indicative, and approved/signed figures are not necessarily disbursements. Changes to CSV while paging may change results.'}
