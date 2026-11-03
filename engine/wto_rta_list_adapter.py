"""WTO public list of notified and early-announcement trade agreements."""
import release_runtime
import datetime
import hashlib
import io
import requests
from openpyxl import load_workbook
URL = 'https://rtais.wto.org/UI/ExportAllRTAList.aspx'
SHEETS = {'agreements': 'AllRTAs', 'changes': 'RTA Changes'}

def search(keyword, sheet='agreements', offset=0, limit=20):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('Keyword must contain 1–100 characters')
    if sheet not in SHEETS:
        raise ValueError('Unknown sheet')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    with requests.get(URL, timeout=40, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('WTO workbook request failed: HTTP ' + str(response.status_code))
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > 5000000:
                raise RuntimeError('WTO workbook exceeds 5 MB')
    w = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        if SHEETS[sheet] not in w.sheetnames:
            raise RuntimeError('Expected WTO worksheet is missing')
        rows = w[SHEETS[sheet]].iter_rows(values_only=True)
        header = next(rows, None)
        if not header or header[:2] != ('RTA ID', 'RTA Name') or len(header) != len(set(header)):
            raise RuntimeError('Unexpected WTO workbook columns')
        matched = []
        for row in rows:
            if not any((keyword.casefold() in str(v).casefold() for v in row if v is not None)):
                continue
            item = {k: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for k, v in zip(header, row)}
            matched.append(item)
        return {'source': 'WTO RTA database workbook', 'source_url': URL, 'source_info': 'https://data.wto.org/en/dataset/ext_rta', 'sha256': hashlib.sha256(content).hexdigest(), 'file_bytes': len(content), 'worksheet': SHEETS[sheet], 'keyword': keyword, 'matched_total': len(matched), 'offset': offset, 'limit': limit, 'items': matched[offset:offset + limit], 'note': '在指定工作表所有原始单元格中不区分大小写搜索子串；仅该工作簿，名称未含关键词的多边协议仍可能在签署方列找到，也可能因组织名称而漏掉。目录状态包括协商阶段，不等于现行对特定成员已生效或能直接享惠；日期须核协定原文及成员生效情况。空值不为零；数据以 WTO 已通知及早期公布信息为范围。'}
    finally:
        w.close()
