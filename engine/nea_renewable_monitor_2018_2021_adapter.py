"""National Energy Administration renewable power monitoring report, 2023."""
import release_runtime
import hashlib, io, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import requests
NOTICE2023 = 'https://zfxxgk.nea.gov.cn/2024-10/10/c_1310787115.htm'
URL2023 = 'https://zfxxgk.nea.gov.cn/1310787115_17307953361061n.doc'
TITLES2023 = ['2023年可再生能源电力消纳总量责任权重完成情况', '2023年可再生能源电力消纳非水电责任权重完成情况', '2023年全国风电并网消纳情况', '2023年全国光伏并网消纳情况', '2023年全国主要流域水电利用情况', '2023年直流特高压线路输送电量情况']
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SOURCES = {2018: ('https://zfxxgk.nea.gov.cn/auto87/201906/t20190610_3673.htm', 'https://zfxxgk.nea.gov.cn/auto87/201906/P020190610510306238174.docx'), 2019: ('https://zfxxgk.nea.gov.cn/2020-05/06/c_139059627.htm', 'https://zfxxgk.nea.gov.cn/139059627_15895345721861n.doc'), 2020: ('https://zfxxgk.nea.gov.cn/2021-06/20/c_1310039970.htm', 'https://zfxxgk.nea.gov.cn/1310039970_16252179582651n.docx'), 2021: ('https://www.nea.gov.cn/2022-09/16/c_1310663387.htm', 'https://www.nea.gov.cn/1310663387_16633279405281n.docx')}
TITLES = {2018: ['各省（区、市）可再生能源电力消纳情况', '各省（区、市）非水电可再生能源电力消纳情况', '风电重点地区最低保障收购年利用小时数落实情况', '光伏发电重点地区最低保障收购年利用小时数落实情况', '清洁能源消纳目标完成情况', '特高压线路输送电量情况'], 2019: ['各省（区、市）可再生能源电力消纳情况', '各省（区、市）非水电可再生能源电力消纳情况', '风电重点地区最低保障收购年利用小时数落实情况', '光伏发电重点地区最低保障收购年利用小时数落实情况', '清洁能源消纳目标完成情况', '特高压线路输送电量情况'], 2020: ['可再生能源电力消纳总量责任权重完成情况', '可再生能源电力消纳非水电责任权重完成情况', '风电重点地区最低保障收购年利用小时数落实情况', '光伏发电重点地区最低保障收购年利用小时数落实情况', '清洁能源消纳目标完成情况', '特高压线路输送电量情况'], 2021: ['可再生能源电力消纳总量责任权重完成情况', '可再生能源电力消纳非水电责任权重完成情况', '全国风电重点地区年利用小时数情况', '全国光伏重点地区年利用小时数情况', '全国风电并网消纳情况', '全国光伏并网消纳情况', '全国主要流域水电利用情况', '直流特高压线路输送电量情况']}

def catalog(year):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2018–2021')
    return [{'table_number': i, 'title': str(year) + '年' + title} for i, title in enumerate(TITLES[year], 1)]

def tables(year, keyword='', table_number=None):
    catalog(year)
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if table_number is not None and (type(table_number) is not int or not 1 <= table_number <= len(TITLES[year])):
        raise ValueError('invalid table_number')
    notice, url = SOURCES[year]
    with requests.get(url, stream=True, timeout=(10, 45), allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 10000000:
                raise ValueError('document too large')
    raw = bytes(data)
    if year != 2019:
        if not raw.startswith(b'PK\x03\x04'):
            raise ValueError('expected DOCX')
        converted = raw
    else:
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
    if len(raw_tables) != len(TITLES[year]):
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
        results.append({'table_number': n, 'title': str(year) + '年' + TITLES[year][n - 1], 'total_rows': len(rows), 'headers': rows[:1], 'rows': matches})
    return {'year': year, 'source': '国家能源局全国可再生能源电力发展监测评价报告', 'notice_url': notice, 'source_url': url, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'tables': results, 'note': '各年度报告表项和表号不同，2021报告含2020–2021省级风光实际利用率。统计口径及单位以对应表头和报告正文为准，保留原始单元格及合并信息，不自动推算；2019 DOC通过本地LibreOffice转换。'}
