"""司法部国家行政法规库公开检索与正文。"""
import release_runtime
import re
import subprocess
from urllib.parse import urlencode
from bs4 import BeautifulSoup
BASE = 'https://xzfg.moj.gov.cn'

def _fetch(path, params):
    url = BASE + path + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('法规库请求失败: ' + p.stderr.strip())
    return (url, BeautifulSoup(p.stdout, 'html.parser'))

def search(keyword, page=1, mode='title'):
    """检索现行有效法规；mode 为 title（标题）或 full（全文）。"""
    if not keyword or not keyword.strip() or len(keyword) > 30:
        raise ValueError('关键词须为 1—30 个字符')
    page = int(page)
    if page < 1 or mode not in ('title', 'full'):
        raise ValueError('页码或检索模式无效')
    kind = '1' if mode == 'title' else '2'
    url, soup = _fetch('/SearchTitleFront' if mode == 'title' else '/SearchFront', {'SiteID': '122', 'Query': keyword, 'Type': kind, 'QueryAll': keyword + 'ZVING' + kind, 'PageIndex': page})
    total = soup.select_one('#law-total')
    if total is None:
        raise RuntimeError('未识别检索结果，页面结构可能已变化或访问受限')
    try:
        count = int(total.get('value'))
    except (ValueError, TypeError):
        raise RuntimeError('未识别有效的检索总数') from None
    if count < 0:
        raise RuntimeError('检索总数不能为负')
    records = []
    for item in soup.select('ul.searching-results-list > li.list-item'):
        a = item.select_one('.title a')
        if not a:
            continue
        mid = re.search('LawID=(\\d+)', a.get('href', ''))
        records.append({'id': mid.group(1) if mid else None, 'title': a.get_text(' ', strip=True).replace(' ', ''), 'url': a.get('href'), 'dates': [n.get_text(' ', strip=True) for n in item.select('.info-list li')], 'history': [{'date': n.get('data-time'), 'title': n.get_text(' ', strip=True), 'url': n.a.get('href') if n.a else None, 'current': bool(n.select_one('a.on'))} for n in item.select('.incident-record')]})
    if len(records) > count or (not records and (page - 1) * 10 < count):
        raise RuntimeError('检索总数与本页结果不一致，无法判定为空')
    return {'source': url, 'total': count, 'page': page, 'results': records, 'legal_status_note': '检索和沿革信息仅供参考，是否现行有效及实施日期请核对正式文本和官网最新状态。'}

def detail(law_id):
    """按 LawID 读取正文及沿革；调用者必须区分当前和历史版本。"""
    if not re.fullmatch('\\d+', str(law_id)):
        raise ValueError('LawID 须为数字')
    url, soup = _fetch('/front/law/detail', {'LawID': law_id})
    title = soup.select_one('.text-title')
    content = soup.select_one('.law-chapter')
    if title is None or content is None:
        raise RuntimeError('未识别法规正文，页面结构可能已变化或访问受限')
    return {'source': url, 'id': str(law_id), 'title': title.get_text(' ', strip=True), 'text': content.get_text('\n', strip=True), 'history': [{'date': n.get('data-time'), 'title': n.get_text(' ', strip=True), 'url': n.a.get('href') if n.a else None, 'selected': bool(n.select_one('a.on'))} for n in soup.select('.incident-record')], 'legal_status_note': 'selected 仅标识当前打开的沿革版本，不代表该版本现行有效；请核对官网最新状态与实施日期。', 'word': BASE + '/law/download?' + urlencode({'LawID': law_id}), 'pdf': BASE + '/law/download?' + urlencode({'LawID': law_id, 'type': 'pdf'})}
