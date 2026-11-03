"""WTO official dispute key stages workbook; preserve cells and date format."""
import release_runtime
import datetime, io, re
import requests, openpyxl
URL = 'https://www.wto.org/english/tratop_e/dispu_e/dates_of_key_stages_e.xlsx'
CATALOG = 'https://data.wto.org/en/dataset/ds_db'
NOTE = 'WTO 官方争端关键程序阶段表，日期单元格按 Excel 类型转为 ISO 并附原数字格式，字符串日期原样保留；空白表示原表空白，不得推断未发生程序。此源表可能滞后于官网，最后记录不代表目前全部争端；当前文件不是历史时点快照，请核查官方案件详情、裁决文书与后续程序。'

def _cell(c):
    v = c.value
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        v = v.isoformat()
    return {'value': v, 'number_format': c.number_format} if v is not None else None

def stages(keyword='', case_id='', offset=0, limit=20, session=None):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词最多 200 字符')
    if not isinstance(case_id, str) or (case_id and (not re.fullmatch('DS\\d{1,5}', case_id.upper()))):
        raise ValueError('争端编号应形如 DS2')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('起始行须为非负整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页须为 1 至 100 行')
    with (session or requests).get(URL, timeout=40, stream=True, headers={'User-Agent': 'PersonalResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 10 * 1024 * 1024:
                raise ValueError('官方工作簿超过 10 MiB')
        source_url = r.url
        modified = r.headers.get('Last-Modified')
    w = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        s = w.active
        rows = list(s.iter_rows())
        headers = [[_cell(c) for c in row] for row in rows[:2]]
        records = []
        term = keyword.strip().casefold()
        for row in rows[2:]:
            v = row[0].value
            if not isinstance(v, str) or not re.fullmatch('DS\\s*\\d+', v.strip(), re.I):
                continue
            norm = re.sub('\\s+', '', v).upper()
            if case_id and norm != case_id.upper():
                continue
            if term and (not any((term in str(c.value or '').casefold() for c in row))):
                continue
            records.append([_cell(c) for c in row])
    finally:
        w.close()
    return {'source': 'WTO dates of key stages in dispute settlement proceedings', 'source_url': source_url, 'catalog': CATALOG, 'http_last_modified': modified, 'note': NOTE, 'header_rows': headers, 'total_matched_rows': len(records), 'offset': offset, 'limit': limit, 'rows': records[offset:offset + limit]}
