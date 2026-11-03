"""浙江省司法厅行政规范性文件库省级默认分类搜索与部分 PDF。"""
import release_runtime
import io, re
import requests
from pypdf import PdfReader
BASE = 'https://zjsftbascweb.zjsft.gov.cn/data/zjdatabase/census/fLibrary/'
STATUSES = {0: '有效', 1: '财税、收费内容执行现规定', 2: '暂时保留', 3: '失效', 4: '废止', 5: '不作为规范性文件管理', 6: '拟修改', 7: '不作为行政规范性文件管理'}

def zhejiang_normative_search(query, page=1, page_size=15, status=None, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('标题关键词须为 1–200 字')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or not 1 <= page <= 100 or (not 1 <= page_size <= 50):
        raise ValueError('页码须为 1–100、每页 1–50 条')
    if status is not None and (isinstance(status, bool) or status not in STATUSES):
        raise ValueError('status 须为空或 0–7 中的数字')
    data = {'docTitle': query.strip(), 'area': 'ZJS', 'deptClass': '10', 'timeLines': status, 'page': {'pageSize': page_size, 'pageNum': page}}
    r = requests.post(BASE + 'getDocPage', json=data, timeout=timeout)
    r.raise_for_status()
    payload = r.json().get('result', {})
    if payload.get('code') != 4000 or not isinstance(payload.get('data'), dict):
        raise ValueError('浙江规范文件库返回异常')
    d = payload['data']
    rows = d.get('rows')
    total = d.get('total')
    if not isinstance(rows, list) or not isinstance(total, int):
        raise ValueError('文件目录结构异常')
    for x in rows:
        if status is not None and x.get('timeLines') != status:
            raise ValueError('返回状态与筛选不一致')
    return {'source': '浙江省司法厅行政规范性文件数据库，网站默认省级分类', 'source_url': BASE + 'getDocPage', 'query': query.strip(), 'page': page, 'page_size': page_size, 'status_filter': status, 'upstream_total': total, 'items': rows, 'note': '使用站方默认 area=ZJS、deptClass=10，不代表其他地区及全部法规；字段 isShowDetail、sourceType 决定原站访问方式。时效显示以来源发布时为准，具体效力及后续变化须核对原文。'}

def zhejiang_normative_pdf(document_id, include_text=False, timeout=35):
    if not isinstance(document_id, str) or not re.fullmatch('[A-Za-z0-9-]{1,80}', document_id):
        raise ValueError('文档 ID 无效')
    if not isinstance(include_text, bool):
        raise ValueError('include_text 须为布尔值')
    url = BASE + 'getBgProvinceFile'
    params = {'sourceType': 4, 'flId': document_id}
    r = requests.get(url, params=params, stream=True, timeout=timeout, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200:
        raise ValueError('PDF 返回重定向或异常状态')
    data = bytearray()
    for chunk in r.iter_content(65536):
        data.extend(chunk)
        if len(data) > 20 * 1024 * 1024:
            raise ValueError('PDF 超过 20 MiB')
    if not data.startswith(b'%PDF-'):
        raise ValueError('来源未返回 PDF；此接口只支持原站 sourceType=4 文件')
    out = {'source': '浙江省司法厅行政规范性文件数据库 PDF', 'source_url': r.url, 'id': document_id, 'note': '仅支持 sourceType=4 的文件；PDF 文字提取可能遗漏图片、图表与排版，文件效力需核对。'}
    if include_text:
        doc = PdfReader(io.BytesIO(data))
        out['pages'] = [{'page': i + 1, 'text': p.extract_text() or ''} for i, p in enumerate(doc.pages)]
    return out
