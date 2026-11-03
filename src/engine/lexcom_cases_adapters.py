"""司法部法通网涉外法律服务典型案例。"""
import release_runtime
import json
import re
import subprocess
from io import BytesIO
from urllib.parse import urlencode
from pypdf import PdfReader
BASE = 'https://lexcom.12348.gov.cn/api/'

def _curl(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '15000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('法通网请求失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 15000000:
        raise RuntimeError('响应超过 15 MB')
    return (url, p.stdout)

def _json(path, params=None):
    url, body = _curl(path, params)
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise RuntimeError('返回非 JSON，可能访问受限或接口变化') from exc
    if data.get('code') not in ('0', 0):
        raise RuntimeError('法通网返回错误: ' + str(data.get('msg')))
    return data['data']

def search(keyword='', page=1, size=20, province=''):
    """按关键词或省份搜索涉外法律服务典型案例。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量为 1—100')
    params = {'current': page, 'size': size}
    if keyword:
        params['keyword'] = keyword
    if province:
        params['province'] = province
    result = _json('portal/lr/case/page', params)
    if not isinstance(result, dict) or not isinstance(result.get('records'), list):
        raise RuntimeError('案例检索结构变化')
    return {**result, 'toolkit_source_url': BASE + 'portal/lr/case/page?' + urlencode(params), 'toolkit_note': '司法部涉外法律服务案例目录，不等于法院裁判文书全集；总数与页码为源站返回，目录更新可能改变跨页顺序。'}

def detail(case_id):
    if not re.fullmatch('\\d+', str(case_id)):
        raise ValueError('案例 ID 须为数字')
    return _json('portal/lr/case/query', {'id': case_id})

def pdf_text(file_id):
    """按详情返回的附件 ID 提取 PDF 逐页文字。"""
    if not re.fullmatch('\\d+', str(file_id)):
        raise ValueError('附件 ID 须为数字')
    url, raw = _curl('attachment/preview/' + str(file_id))
    if not raw.startswith(b'%PDF'):
        raise RuntimeError('附件不是 PDF 或当前不可读取')
    doc = PdfReader(BytesIO(raw))
    return {'source': url, 'pages': len(doc.pages), 'text_by_page': [x.extract_text() or '' for x in doc.pages]}
