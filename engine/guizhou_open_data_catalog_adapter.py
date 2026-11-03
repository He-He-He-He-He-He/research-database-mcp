"""贵州省政府数据开放平台目录和无条件开放 XLSX 预览。"""
import release_runtime
import base64
import io
import re
import zipfile
from datetime import date, datetime, time
import requests
import openpyxl
BASE = 'https://data.guizhou.gov.cn/api/'

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9-]{1,80}', value):
        raise ValueError('资源标识无效')
    return value

def _json(path, body=None, params=None):
    if body is None:
        r = requests.get(BASE + path, params=params, timeout=30, allow_redirects=False)
    else:
        r = requests.post(BASE + path, json=body, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('官网响应重定向')
    try:
        x = r.json()
    except ValueError as exc:
        raise RuntimeError('官网响应非 JSON') from exc
    if not isinstance(x, dict) or x.get('status') != 200:
        raise RuntimeError('官网数据服务未成功响应')
    return x

def search(keyword='', page=1, size=12):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or isinstance(size, bool) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('页码或每页条数无效')
    p = {'orderBy': 0, 'topicId': [], 'orgId': [], 'pageSize': size, 'scenarioId': '', 'resourceType': '', 'resourceFormats': [], 'openAttribute': '', 'searchText': [keyword] if keyword else [], 'pageIndex': page, 'path': None}
    result = _json('search/data/getDataListByParams', body=p)
    rows = result.get('data')
    total = result.get('total')
    if not isinstance(rows, list) or not isinstance(total, int) or isinstance(total, bool) or (total < 0) or (result.get('pageIndex') != page) or (result.get('pageSize') != size) or (len(rows) > size) or (not rows and (page - 1) * size < total):
        raise RuntimeError('目录总数、分页或条目异常')
    keys = ('id', 'name', 'description', 'orgName', 'topicName', 'openAttribute', 'resourceFormats', 'updateTime', 'timeRange')
    items = [{k: x.get(k) for k in keys} for x in rows]
    literal_count = sum((1 for x in items if keyword and any((keyword.casefold() in str(v).casefold() for v in x.values() if v is not None))))
    return {'source': '贵州省政府数据开放平台', 'keyword': keyword, 'page': page, 'size': size, 'total': total, 'literal_matches_on_page': literal_count, 'items': items, 'note': '官网结果可能为宽泛分词或无字面匹配；total 是上游总数，不是精确匹配数。literal_matches_on_page 仅检查本页返回的元数据字段。目录含有条件资源，不能代表数据已取得；openAttribute=2 在本次样本中对应无条件开放，预览前仍核详情。'}

def preview(dataset_id, resource_id, max_rows=100):
    _id(dataset_id)
    _id(resource_id)
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or (not 1 <= max_rows <= 1000):
        raise ValueError('返回行数须为1至1000')
    d = _json('search/data/getDataDetailByDataId', body={'id': dataset_id}).get('data')
    if not isinstance(d, dict) or d.get('id') != dataset_id or d.get('openAttribute') != 2:
        raise ValueError('仅支持官网标为无条件开放的数据集')
    matches = [x for x in d.get('resourceList', []) if isinstance(x, dict) and x.get('id') == resource_id and (x.get('dataId') == dataset_id)]
    if len(matches) != 1 or str(matches[0].get('resourceFormat', '')).lower() != 'xlsx':
        raise ValueError('该数据集下未找到唯一 XLSX 资源')
    result = _json('interface/online/previewFile', params={'id': resource_id})
    encoded = result.get('data')
    if not isinstance(encoded, str) or len(encoded) > 14000000:
        raise RuntimeError('预览文件无效或过大')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise RuntimeError('预览文件编码无效') from exc
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos = z.infolist()
            if len(infos) > 1000 or sum((i.file_size for i in infos)) > 50000000:
                raise RuntimeError('预览 XLSX 解压规模过大')
        w = openpyxl.load_workbook(io.BytesIO(raw), read_only=False, data_only=True)
    except (zipfile.BadZipFile, ValueError) as exc:
        raise RuntimeError('预览不是有效 XLSX') from exc

    def scalar(v):
        return v.isoformat() if isinstance(v, (date, datetime, time)) else v
    sheets = []
    try:
        for s in w.worksheets:
            if s.max_column > 200 or s.max_row > 100000:
                raise RuntimeError('预览表格维度超限')
            sheets.append({'name': s.title, 'rows': [[scalar(c.value) for c in row] for row in s.iter_rows(min_row=1, max_row=min(s.max_row, max_rows))], 'sheet_rows': s.max_row, 'merged_ranges': [str(x) for x in s.merged_cells.ranges]})
    finally:
        w.close()
    return {'source': '贵州省政府数据开放平台', 'dataset_id': dataset_id, 'resource_id': resource_id, 'title': d.get('name'), 'provider': d.get('orgName'), 'updateTime': d.get('updateTime'), 'sheets': sheets, 'note': '官网预览文件，不保证是完整下载文件；每个工作表最多返回 max_rows 行。保留合并范围，空单元格不是零；历史时段及使用许可须核对原站。'}
