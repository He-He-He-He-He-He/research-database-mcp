"""US FEC all-candidate financial summaries by election cycle, public bulk ZIP."""
import release_runtime
import csv
import hashlib
import io
import re
import zipfile
import requests
ROOT = 'https://www.fec.gov/files/bulk-downloads/'
DOC = 'https://www.fec.gov/campaign-finance-data/all-candidates-file-description/'
FIELDS = ['CAND_ID', 'CAND_NAME', 'CAND_ICI', 'PTY_CD', 'CAND_PTY_AFFILIATION', 'TTL_RECEIPTS', 'TRANS_FROM_AUTH', 'TTL_DISB', 'TRANS_TO_AUTH', 'COH_BOP', 'COH_COP', 'CAND_CONTRIB', 'CAND_LOANS', 'OTHER_LOANS', 'CAND_LOAN_REPAY', 'OTHER_LOAN_REPAY', 'DEBTS_OWED_BY', 'TTL_INDIV_CONTRIB', 'CAND_OFFICE_ST', 'CAND_OFFICE_DISTRICT', 'SPEC_ELECTION', 'PRIM_ELECTION', 'RUN_ELECTION', 'GEN_ELECTION', 'GEN_ELECTION_PRECENT', 'OTHER_POL_CMTE_CONTRIB', 'POL_PTY_CONTRIB', 'CVG_END_DT', 'INDIV_REFUNDS', 'CMTE_REFUNDS']

def _load(cycle):
    url = ROOT + str(cycle) + '/weball' + str(cycle)[-2:] + '.zip'
    r = requests.get(url, timeout=45, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for b in r.iter_content(65536):
        size += len(b)
        if size > 10000000:
            raise ValueError('archive exceeds 10 MB')
        parts.append(b)
    raw = b''.join(parts)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = [x for x in z.infolist() if not x.is_dir() and x.filename.lower().endswith('.txt')]
        if len(entries) != 1 or entries[0].file_size > 20000000:
            raise ValueError('unexpected archive')
        text = z.read(entries[0]).decode('utf-8-sig')
    rows = []
    for row in csv.reader(io.StringIO(text, newline=''), delimiter='|'):
        if len(row) != len(FIELDS):
            raise ValueError('unexpected FEC row schema')
        rows.append(dict(zip(FIELDS, row)))
    return (url, r.headers.get('Last-Modified'), hashlib.sha256(raw).hexdigest(), rows)

def search(cycle, keyword='', state='', limit=20, offset=0):
    if isinstance(cycle, bool) or not isinstance(cycle, int) or (not 1980 <= cycle <= 2100) or cycle % 2:
        raise ValueError('cycle must be an even election year from 1980')
    if not isinstance(keyword, str) or len(keyword) > 120 or (not isinstance(state, str)) or (state and (not re.fullmatch('[A-Z]{2}', state))):
        raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    url, modified, digest, rows = _load(cycle)
    chosen = [r for r in rows if keyword.casefold() in (r['CAND_NAME'] + ' ' + r['CAND_ID']).casefold() and (not state or r['CAND_OFFICE_ST'] == state)]
    return {'source': url, 'documentation': DOC, 'cycle': cycle, 'last_modified': modified, 'archive_sha256': digest, 'dataset_rows': len(rows), 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'US FEC campaign-reported financial summaries for candidates raising or spending in the cycle regardless of election year; not election results. Transfers among authorized committees can be counted twice; receipts, spending, loans and balances overlap and should not be summed blindly. Coverage end date varies by candidate. Original numeric strings, signs and missing values are preserved; entire cycle file filtered locally.'}
