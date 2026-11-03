"""U.S. Census 2023 CBP national data from the public downloadable CSV archive."""
import release_runtime
import csv, io, re, zipfile
import requests
URL = 'https://www2.census.gov/programs-surveys/cbp/datasets/2023/cbp23us.zip'

def industry(naics='------'):
    if not isinstance(naics, str) or not re.fullmatch('[0-9-]{6}', naics):
        raise ValueError('naics must be the six-character source code, e.g. ------ or 72----')
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 5000000:
                raise ValueError('Archive too large')
            chunks.append(chunk)
    with zipfile.ZipFile(io.BytesIO(b''.join(chunks))) as z:
        files = [i for i in z.infolist() if i.filename == 'cbp23us.txt']
        if len(files) != 1 or files[0].file_size > 50000000:
            raise ValueError('Unexpected archive structure')
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            expected = {'uscode', 'naics', 'lfo', 'emp_nf', 'emp', 'qp1_nf', 'qp1', 'ap_nf', 'ap', 'est'}
            if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                raise ValueError('Unexpected source columns')
            rows = [row for row in reader if row['uscode'] == '98' and row['naics'] == naics and (row['lfo'] == '-')]
    if len(rows) > 1:
        raise ValueError('Source returned duplicate national all-organization rows')
    return {'source_url': URL, 'source': 'U.S. Census Bureau CBP 2023 national CSV', 'naics': naics, 'items': rows, 'note': 'Paid-employee establishments, not firms or all businesses. Employment is March 12 pay period; annual payroll is in thousands of US dollars. Preserve original noise/suppression flags; no matching row does not mean zero.'}
