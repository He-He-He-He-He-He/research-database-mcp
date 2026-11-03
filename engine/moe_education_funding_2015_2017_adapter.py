"""MOE 2015–2017 provincial education expenditure tables."""
import release_runtime
import io, zipfile, tempfile, subprocess, shutil, hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
import requests
SOURCES = {2015: 'https://hudong.moe.gov.cn/srcsite/A05/s3040/201611/W020161110551318226819.docx', 2016: 'https://hudong.moe.gov.cn/srcsite/A05/s3040/201710/W020171025362950481325.doc', 2017: 'https://hudong.moe.gov.cn/srcsite/A05/s3040/201810/W020181012594998889329.doc'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def catalog():
    return [{'year': y, 'url': u, 'format': 'docx' if y == 2015 else 'doc'} for y, u in SOURCES.items()]

def tables(year, keyword=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2015–2017')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    with requests.get(SOURCES[year], timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 10000000:
                raise ValueError('document too large')
    raw = bytes(data)
    if year != 2015:
        if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
            raise ValueError('expected binary DOC')
        executable = shutil.which('soffice')
        if not executable:
            raise RuntimeError('DOC conversion requires LibreOffice soffice')
        with tempfile.TemporaryDirectory(prefix='moe_education_') as d:
            root = Path(d)
            source = root / 'source.doc'
            source.write_bytes(raw)
            out = root / 'out'
            out.mkdir()
            profile = (root / 'profile').as_uri()
            cmd = [executable, '-env:UserInstallation=' + profile, '--headless', '--convert-to', 'docx', '--outdir', str(out), str(source)]
            p = release_runtime.run(cmd, capture_output=True, timeout=60)
            result = out / 'source.docx'
            if p.returncode or not result.exists():
                raise RuntimeError('LibreOffice DOC conversion failed')
            data = result.read_bytes()
            if len(data) > 10000000:
                raise ValueError('converted document too large')
    else:
        data = raw
    if not data.startswith(b'PK\x03\x04'):
        raise ValueError('invalid DOCX')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.getinfo('word/document.xml').file_size > 12000000:
            raise ValueError('document XML too large')
        root = ET.fromstring(z.read('word/document.xml'))
    result = []
    for n, t in enumerate(root.iter(W + 'tbl'), 1):
        rows = []
        for i, tr in enumerate(t.findall(W + 'tr'), 1):
            cells = []
            for tc in tr.findall(W + 'tc'):
                text = ''.join((x.text or '' for x in tc.iter(W + 't')))
                props = tc.find(W + 'tcPr')
                span = props.find(W + 'gridSpan') if props is not None else None
                merge = props.find(W + 'vMerge') if props is not None else None
                cells.append({'text': text.strip(), 'colspan': int(span.get(W + 'val', '1')) if span is not None else 1, 'vertical_merge': None if merge is None else merge.get(W + 'val', 'continue')})
            rows.append({'row': i, 'cells': cells})
        q = ''.join(keyword.split())
        matches = [row for row in rows if q in ''.join((''.join(c['text'].split()) for c in row['cells']))]
        result.append({'table_number': n, 'total_rows': len(rows), 'headers': rows[:2], 'rows': matches})
    if len(result) != 5:
        raise ValueError('expected five original tables')
    return {'year': year, 'source': '教育部、国家统计局、财政部全国教育经费执行情况统计表', 'source_url': SOURCES[year], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'tables': result, 'note': '五张原表按来源次序及原表头解释，不同年份公共财政与一般公共预算名称不同；2016–17 DOC通过本地LibreOffice转换，保留单元格及合并，不自动推断数值含义；公报注释和统计口径需核源。'}
