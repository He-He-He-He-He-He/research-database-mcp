"""US DOL O*NET 31.0 occupation descriptions, tasks and software skills."""
import release_runtime
import csv, io, hashlib, re
import requests
BASE = 'https://www.onetcenter.org/dl_files/database/db_31_0_csv/'
FILES = {'occupations': 'occupation_data.csv', 'tasks': 'task_statements.csv', 'software': 'software_skills.csv'}

def search(dataset, keyword='', code='', limit=50, offset=0):
    if dataset not in FILES or not isinstance(keyword, str) or len(keyword) > 200 or (not isinstance(code, str)) or (code and (not re.fullmatch('\\d{2}-\\d{4}\\.\\d{2}', code))) or (type(limit) is not int) or (not 1 <= limit <= 500) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('Invalid dataset, keyword, occupation code or pagination')
    url = BASE + FILES[dataset]
    with requests.get(url, timeout=45, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for x in r.iter_content(65536):
            raw.extend(x)
            if len(raw) > 8000000:
                raise ValueError('Data file exceeds size limit')
        modified = r.headers.get('Last-Modified')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or 'O*NET-SOC Code' not in reader.fieldnames or 'Title' not in reader.fieldnames:
        raise ValueError('Unexpected CSV header')
    q = keyword.casefold().strip()
    matched = []
    total = 0
    for row in reader:
        total += 1
        if code and row['O*NET-SOC Code'] != code:
            continue
        if q and q not in ' '.join((str(v or '') for v in row.values())).casefold():
            continue
        matched.append(row)
    return {'source': url, 'dataset': dataset, 'version': '31.0', 'sha256': hashlib.sha256(raw).hexdigest(), 'last_modified_header': modified, 'columns': reader.fieldnames, 'source_total': total, 'matched_total': len(matched), 'offset': offset, 'returned': len(matched[offset:offset + limit]), 'records': matched[offset:offset + limit], 'notes': ['O*NET is sponsored by the US Department of Labor/Employment and Training Administration, developed by National Center for O*NET Development. It describes US occupations; it is not employment, wage or job-vacancy counts.', 'Occupation, tasks and software skills are different files; task source and date must be interpreted per record. Hot Technology and In Demand have distinct job-posting definitions.', 'Version 31.0 and file modification date are not proof of availability at an earlier historical cutoff. Empty results are not evidence an occupation or skill does not exist.', 'Database content generally CC BY 4.0 with exceptions; credit O*NET 31.0 Database and USDOL/ETA, link license and disclose modifications: https://www.onetcenter.org/license_db.html']}
