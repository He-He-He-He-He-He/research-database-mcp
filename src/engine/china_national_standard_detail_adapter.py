"""国家标准全文公开系统：读取官方国家标准详情题录。"""
import release_runtime
import re, requests
from bs4 import BeautifulSoup
URL = 'https://openstd.samr.gov.cn/bzgk/std/newGbInfo'

def detail(hcno):
    if not isinstance(hcno, str) or not re.fullmatch('[A-Fa-f0-9]{32}', hcno):
        raise ValueError('标准 ID 须为 32 位十六进制')
    with requests.get(URL, params={'hcno': hcno}, timeout=25, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('官方详情发生跳转，请核验')
        r.raise_for_status()
        parts = []
        n = 0
        for b in r.iter_content(65536):
            n += len(b)
            if n > 2000000:
                raise ValueError('页面过大')
            parts.append(b)
    soup = BeautifulSoup(b''.join(parts).decode('utf-8', 'replace'), 'html.parser')
    title = soup.find('h1')
    number = title.get_text(' ', strip=True).removeprefix('标准号：').strip() if title else ''
    fields = []
    for label in ('中文标准名称', '英文标准名称', '标准状态'):
        node = soup.find(string=lambda s: s and label + '：' in s)
        if node:
            text = node.parent.get_text(' ', strip=True)
            fields.append({'name': label, 'value': text.split('：', 1)[-1].strip()})
    for label in soup.select('div.title'):
        sibling = label.find_next_sibling('div', class_='content')
        if sibling:
            fields.append({'name': label.get_text(' ', strip=True), 'value': sibling.get_text(' ', strip=True)})
    if not number or not any((x['name'] == '标准状态' and x['value'] for x in fields)):
        raise RuntimeError('官方详情结构未识别或访问受限')
    buttons = [b.get_text(' ', strip=True) for b in soup.find_all('button') if b.get_text(' ', strip=True) in ('在线预览', '下载标准')]
    return {'source_url': URL + '?hcno=' + hcno, 'id': hcno, 'standard_number': number, 'fields': fields, 'page_buttons': buttons, 'note': '状态及日期为本次访问时官网显示，不自动代表历史时点状态；发布与实施日期不同。页面按钮仅表示页面列出该操作，未验证全文可访问、下载或使用许可；标准有效性、替代和适用范围应核对官方最新信息。'}
