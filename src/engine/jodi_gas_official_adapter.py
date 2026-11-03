"""Read JODI-Gas public ZIP snapshot, preserving units and assessment flags."""
import release_runtime
import csv, io, re, zipfile, requests
URL = 'https://www.jodidata.org/jodi-publisher/gas/28/GAS_world_NewFormat.zip'
PAGE = 'https://www.jodidata.org/gas/database/data-downloads.aspx'
GUIDE = 'https://www.jodidata.org/_resources/files/downloads/gas-data/jodi-gas-wdb-short--long-names-ver2025.pdf'

def data(country, start, end, flow='', unit='', offset=0, limit=20):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
        raise ValueError('Country must be a two-letter code')
    for x in (start, end):
        if not isinstance(x, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', x):
            raise ValueError('Dates must be YYYY-MM')
    if start > end:
        raise ValueError('Dates must be ordered')
    for v in (flow, unit):
        if not isinstance(v, str) or (v and (not re.fullmatch('[A-Z0-9]{1,20}', v))):
            raise ValueError('Invalid flow or unit')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0 or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    with requests.get(URL, stream=True, timeout=(15, 45)) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > 10000000:
                raise RuntimeError('JODI-Gas ZIP too large')
            chunks.append(chunk)
    out = []
    count = 0
    with zipfile.ZipFile(io.BytesIO(b''.join(chunks))) as z:
        files = [x for x in z.infolist() if x.filename.lower().endswith('.csv') and (not x.is_dir())]
        if len(files) != 1 or files[0].file_size > 100000000:
            raise RuntimeError('Unexpected JODI-Gas ZIP contents')
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            if set(reader.fieldnames or []) != {'REF_AREA', 'TIME_PERIOD', 'ENERGY_PRODUCT', 'FLOW_BREAKDOWN', 'UNIT_MEASURE', 'OBS_VALUE', 'ASSESSMENT_CODE'}:
                raise RuntimeError('Unexpected JODI-Gas CSV schema')
            for row in reader:
                if row['REF_AREA'] != country or not start <= row['TIME_PERIOD'] <= end or (flow and row['FLOW_BREAKDOWN'] != flow) or (unit and row['UNIT_MEASURE'] != unit):
                    continue
                if offset <= count < offset + limit:
                    out.append(row)
                count += 1
    return {'source': 'Joint Organisations Data Initiative (JODI-Gas), coordinated by IEF', 'source_page': PAGE, 'download_url': URL, 'code_guide': GUIDE, 'file': files[0].filename, 'matched': count, 'offset': offset, 'items': out, 'note': 'Fixed publisher ZIP URL; latest release is not guaranteed. Natural gas M3 means million cubic metres (at 15 C, 760 mm Hg), not a single cubic metre. Preserve assessment and missing flags; check product/flow/unit and code guide. Values in multiple units or flows may overlap and must not be summed.'}
