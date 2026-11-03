"""司法部公开征求意见系统：已结束的草案列表与详情。"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
from bs4 import BeautifulSoup
BASE = 'https://zqyj.chinalaw.gov.cn/h5/'

def _curl(url, data=None):
    cmd = ['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url]
    if data is not None:
        cmd += ['--data', urlencode(data)]
    p = release_runtime.run(cmd, capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('公开征求意见系统请求失败: ' + p.stderr.strip())
    return p.stdout

def ended(draft_type=1, page=1, keyword='', year=''):
    """查询已结束征求意见草案：1 法律行政法规，2 部门规章。"""
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (page, draft_type))):
        raise ValueError('页码和草案类型须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    page = int(page)
    draft_type = int(draft_type)
    if page < 1 or draft_type not in (1, 2) or (year and (not re.fullmatch('\\d{4}', str(year)))):
        raise ValueError('页码、草案类型或年份无效')
    raw = _curl(BASE + 'bindOverCollectionList', {'pageIndex': page - 1, 'pageSize': 10, 'year': year, 'CollectUnit': '', 'draftType': draft_type, 'Name': keyword})
    try:
        d = json.loads(raw)
    except ValueError as exc:
        raise RuntimeError('系统返回非 JSON，可能有访问限制或接口变更') from exc
    if not isinstance(d, dict):
        raise RuntimeError('系统返回结构异常，无法判断检索结果')
    if d.get('_ZVING_STATUS') != 1:
        raise RuntimeError('查询失败: ' + str(d.get('_ZVING_MESSAGE')))
    if not isinstance(d.get('data'), list) or not isinstance(d.get('total'), int) or isinstance(d.get('total'), bool) or (d['total'] < 0):
        raise RuntimeError('系统未返回有效的结果列表或总数，不能判断是否无结果')
    records = []
    for x in d.get('data', []):
        i = x['id']
        records.append({'id': i, 'title': x.get('name'), 'unit': x.get('collectunitname'), 'start': x.get('starttime'), 'end': x.get('endtime'), 'published': x.get('publishtime'), 'detail_url': BASE + 'readmore?' + urlencode({'listType': 1, 'id': i}), 'explanation_url': BASE + 'draftExplain?' + urlencode({'DraftID': i}) if str(x.get('cexisturl')) == '1' else None})
    return {'source': BASE + 'overCollectionList?draftType=' + str(draft_type), 'draft_type': draft_type, 'page': page, 'total': d['total'], 'results': records, 'legal_status_note': '征求意见稿不是现行有效法规；结束征求意见不代表草案已通过或生效，请查正式公布文本。'}

def detail(draft_id, explanation=False):
    """读取草案正文或说明；不提交意见。"""
    if not isinstance(explanation, bool):
        raise ValueError('explanation 须为布尔值')
    if not re.fullmatch('\\d+', str(draft_id)):
        raise ValueError('草案 ID 必须为数字')
    path = 'draftExplain?' + urlencode({'DraftID': draft_id}) if explanation else 'readmore?' + urlencode({'listType': 1, 'id': draft_id})
    url = BASE + path
    soup = BeautifulSoup(_curl(url), 'html.parser')
    title = soup.select_one('.content-title')
    content = soup.select_one('.con-content')
    if title is None or content is None:
        raise RuntimeError('未识别草案正文，可能需登录或页面已变更')
    return {'source': url, 'title': title.get_text(' ', strip=True), 'metadata': soup.select_one('.con-head').get_text(' ', strip=True) if soup.select_one('.con-head') else '', 'text': content.get_text('\n', strip=True), 'type': '草案说明' if explanation else '征求意见稿', 'legal_status_note': '草案或说明不等于正式公布、现行有效的法规，请核查后续正式文本。'}
