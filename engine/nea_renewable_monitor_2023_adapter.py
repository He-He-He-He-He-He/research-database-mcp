"""National Energy Administration renewable power monitoring report, 2023."""
import release_runtime
import hashlib, io, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import requests
NOTICE = 'https://zfxxgk.nea.gov.cn/2024-10/10/c_1310787115.htm'
URL = 'https://zfxxgk.nea.gov.cn/1310787115_17307953361061n.doc'
TITLES = ['2023年可再生能源电力消纳总量责任权重完成情况', '2023年可再生能源电力消纳非水电责任权重完成情况', '2023年全国风电并网消纳情况', '2023年全国光伏并网消纳情况', '2023年全国主要流域水电利用情况', '2023年直流特高压线路输送电量情况']
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def catalog():
    return [{'table_number': i, 'title': title} for i, title in enumerate(TITLES, 1)]

def tables(keyword='', table_number=None):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if table_number is not None and (type(table_number) is not int or not 1 <= table_number <= 6):
        raise ValueError('table_number must be 1–6')
    with requests.get(URL, stream=True, timeout=(10, 45), allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 10000000:
                raise ValueError('document too large')
    raw = bytes(data)
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('expected binary DOC')
    soffice = shutil.which('soffice')
    if not soffice:
        raise RuntimeError('requires LibreOffice soffice to convert DOC')
    with tempfile.TemporaryDirectory(prefix='nea_monitor_') as d:
        root = Path(d)
        (root / 'source.doc').write_bytes(raw)
        (root / 'out').mkdir()
        cmd = [soffice, '-env:UserInstallation=' + (root / 'profile').as_uri(), '--headless', '--convert-to', 'docx', '--outdir', str(root / 'out'), str(root / 'source.doc')]
        proc = release_runtime.run(cmd, capture_output=True, timeout=60)
        out = root / 'out' / 'source.docx'
        if proc.returncode or not out.exists():
            raise RuntimeError('LibreOffice conversion failed')
        converted = out.read_bytes()
        if len(converted) > 10000000:
            raise ValueError('converted document too large')
    with zipfile.ZipFile(io.BytesIO(converted)) as archive:
        if archive.getinfo('word/document.xml').file_size > 12000000:
            raise ValueError('document XML too large')
        root = ET.fromstring(archive.read('word/document.xml'))
    raw_tables = list(root.iter(W + 'tbl'))
    if len(raw_tables) != 6:
        raise ValueError('unexpected number of tables')
    results = []
    for n, t in enumerate(raw_tables, 1):
        if table_number is not None and n != table_number:
            continue
        rows = []
        for i, tr in enumerate(t.findall(W + 'tr'), 1):
            cells = []
            for tc in tr.findall(W + 'tc'):
                props = tc.find(W + 'tcPr')
                span = props.find(W + 'gridSpan') if props is not None else None
                merge = props.find(W + 'vMerge') if props is not None else None
                cells.append({'text': ''.join((x.text or '' for x in tc.iter(W + 't'))).strip(), 'colspan': int(span.get(W + 'val', '1')) if span is not None else 1, 'vertical_merge': None if merge is None else merge.get(W + 'val', 'continue')})
            rows.append({'row': i, 'cells': cells})
        q = ''.join(keyword.split())
        matches = [row for row in rows if q in ''.join((''.join(c['text'].split()) for c in row['cells']))]
        results.append({'table_number': n, 'title': TITLES[n - 1], 'total_rows': len(rows), 'headers': rows[:1], 'rows': matches})
    return {'source': '国家能源局2023年度全国可再生能源电力发展监测评价报告', 'notice_url': NOTICE, 'source_url': URL, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'tables': results, 'note': '原表为2023年度报告：表3、4、5含2022和2023年对比，其余表主要为2023年或同比信息；地区排序与统计指标以原表头为准。保留原始文本与合并信息，不推算或自动补齐；完整统计口径请阅读原报告。DOC通过本地LibreOffice转换。'}
