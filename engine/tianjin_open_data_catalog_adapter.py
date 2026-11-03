"""天津市信息资源统一开放平台公开数据集目录。"""
import release_runtime
import json
import requests
URL = 'https://open.data.tj.gov.cn/common/sjj.json'

def search(keyword='', page=1, size=20, open_status=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 100):
        raise ValueError('每页须为1至100项')
    if open_status not in ('', '无条件开放', '有条件开放'):
        raise ValueError('开放状态无效')
    with requests.get(URL, stream=True, timeout=(15, 45), allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise RuntimeError('目录来源发生重定向')
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 12000000:
                raise RuntimeError('目录超过大小限制')
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError('官方目录不是有效 JSON') from exc
    if not isinstance(data, dict) or not isinstance(data.get('dataList'), list) or (not isinstance(data.get('allCount'), int)) or isinstance(data['allCount'], bool) or (data['allCount'] != len(data['dataList'])):
        raise RuntimeError('官方目录总数与条目不一致')
    rows = data['dataList']
    if not all((isinstance(x, dict) and isinstance(x.get('title'), str) for x in rows)):
        raise RuntimeError('官方目录条目结构异常')
    matched = [x for x in rows if keyword in x['title'] and (not open_status or x.get('openStatus') == open_status)]
    fields = ('title', 'href', 'documentType', 'subjectName', 'openStatus', 'fromDepartment', 'publishDate', 'updateDate', 'summary', 'areaName')
    return {'source': '天津市信息资源统一开放平台', 'source_url': URL, 'keyword': keyword, 'open_status': open_status, 'catalog_total': len(rows), 'matched_count': len(matched), 'page': page, 'size': size, 'items': [{k: x.get(k) for k in fields} for x in matched[(page - 1) * size:page * size]], 'note': '对官网提供的完整目录在本地按标题和开放状态筛选；时间字段为官网原始毫秒时间戳。目录不等于文件已下载或数据已验证，开放状态和下载要求以详情页为准。'}
