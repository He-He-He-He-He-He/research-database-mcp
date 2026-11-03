"""中国网络视听大会公开行业报告目录与详情。"""
import release_runtime
import re, subprocess
from urllib.parse import urlparse
from bs4 import BeautifulSoup
BASE = 'https://www.vidchina.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.vidchina.cn':
        raise ValueError('仅允许大会官网')
    c = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, timeout=30)
    if c.returncode:
        raise RuntimeError('网络视听大会请求失败: ' + c.stderr.decode('utf-8', 'replace').strip())
    return BeautifulSoup(c.stdout, 'html.parser')

def reports(keyword='', category='0'):
    """读取官网当前可选分类：0 全部、2022—2025、older 更早。"""
    if category not in ('0', '2022', '2023', '2024', '2025', 'older'):
        raise ValueError('不支持的官网分类')
    path = '%E6%9B%B4%E6%97%A9' if category == 'older' else category
    source = f'{BASE}/outcomes/{path}'
    s = _get(source)
    rows = []
    for a in s.select('a[href]'):
        m = re.fullmatch('https://www\\.vidchina\\.cn/outcome/(\\d+)', a['href'])
        title = a.select_one('.outcomes-word')
        if m and title:
            name = title.get_text(' ', strip=True)
            if keyword in name:
                rows.append({'id': m.group(1), 'title': name, 'url': a['href']})
    if not s.select('a[href*="/outcome/"]'):
        raise RuntimeError('未识别报告目录或目录为空')
    return {'source': source, 'category': category, 'total': len(rows), 'records': rows}

def detail(report_id):
    if not re.fullmatch('\\d+', str(report_id)):
        raise ValueError('报告 ID 必须为数字')
    url = f'{BASE}/outcome/{report_id}'
    s = _get(url)
    title = s.select_one('.outcome-show-title')
    metadata = s.select_one('.outcome-show-origin')
    holder = s.select_one('.outcome-show-content .outcome-show-content')
    if title is None:
        raise RuntimeError('未识别报告详情')
    links = []
    for a in s.select('.download a[href]'):
        u = urlparse(a['href'])
        if u.scheme == 'https' and u.hostname == 'cdn.vidchina.cn' and u.path.startswith('/upload/files/'):
            links.append({'title': a.get_text(' ', strip=True), 'url': a['href']})
    return {'source': url, 'title': title.get_text(' ', strip=True), 'metadata': metadata.get_text(' ', strip=True) if metadata else None, 'description': holder.get_text('\n', strip=True) if holder else None, 'attachments': links}
