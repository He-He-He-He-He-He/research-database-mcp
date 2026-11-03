"""NCES IPEDS 2023-24 institutional directory and official data dictionary."""
import release_runtime
import csv
import hashlib
import io
import re
import zipfile
import requests
import openpyxl
ROOT = 'https://nces.ed.gov/ipeds/datacenter/data/'
PAGE = 'https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx?gotoReportId=7&rtid=7&year=2023'
NOTES = ['The file describes the 2023-24 IPEDS institutional universe, not a current accreditation or operating-status list.', 'The NCES catalogue describes the directory as updated January 2026, while the currently downloadable dictionary identifies release 4 as September 2025; retain source timestamps and do not resolve this inconsistency by assumption.', 'Data can include corrections and imputation. Current downloadable bytes do not establish the contents available at a previous date.', 'Preserve raw coded values; use the supplied official dictionary to interpret sector, status, geography and missing-value codes. Inclusion does not establish program quality, accreditation or eligibility.']

def _zip(name, member):
    r = requests.get(ROOT + name, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('NCES did not return ZIP')
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        if member not in z.namelist() or z.getinfo(member).file_size > 30000000:
            raise ValueError('Unexpected NCES ZIP content')
        data = z.read(member)
    return (data, hashlib.sha256(r.content).hexdigest(), r.headers.get('Last-Modified'))

def search(keyword, state='', limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(state, str)) or (state and (not re.fullmatch('[A-Za-z]{2}', state))) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid IPEDS query')
    raw, sha, modified = _zip('HD2023.zip', 'HD2023.csv')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not {'UNITID', 'INSTNM', 'STABBR', 'CONTROL', 'CYACTIVE'} <= set(reader.fieldnames or []):
        raise ValueError('Unexpected IPEDS headers')
    term = keyword.casefold()
    rows = [r for r in reader if (not state or r['STABBR'] == state.upper()) and term in (r['UNITID'] + ' ' + r['INSTNM'] + ' ' + r['IALIAS']).casefold()]
    return {'source': ROOT + 'HD2023.zip', 'catalogue': PAGE, 'sha256': sha, 'http_last_modified': modified, 'columns': reader.fieldnames, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}

def dictionary(variable):
    if not isinstance(variable, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', variable):
        raise ValueError('Invalid variable')
    variable = variable.upper()
    raw, sha, modified = _zip('HD2023_Dict.zip', 'HD2023_dict.xlsx')
    w = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    if not {'Introduction', 'Varlist', 'Frequencies'} <= set(w.sheetnames):
        raise ValueError('Unexpected IPEDS dictionary')
    varlist = list(w['Varlist'].values)
    freq = list(w['Frequencies'].values)
    if tuple(varlist[0][:2]) != ('varNumber', 'varName') or tuple(freq[0][1:4]) != ('VarName', 'CodeValue', 'ValueLabel'):
        raise ValueError('Unexpected dictionary headings')
    return {'source': ROOT + 'HD2023_Dict.zip', 'sha256': sha, 'http_last_modified': modified, 'introduction': [list(r) for r in w['Introduction'].values], 'varlist_columns': varlist[0], 'variables': [list(r) for r in varlist[1:] if r[1] == variable], 'frequency_columns': freq[0], 'codes': [list(r) for r in freq[1:] if r[1] == variable], 'notes': NOTES}
