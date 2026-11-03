"""皮书数据库图书公开书目信息。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup

def detail(book_id):
    if not isinstance(book_id, str) or not re.fullmatch('\\d{1,15}', book_id):
        raise ValueError('图书编号须为数字')
    url = 'https://www.pishu.com.cn/skwx_ps/bookDetail'
    r = requests.get(url, params={'SiteID': '14', 'ID': book_id}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    candidates = []
    for table in soup.find_all('table'):
        fields = []
        for row in table.find_all('tr', recursive=False) or table.select(':scope > tbody > tr'):
            cells = row.find_all('td', recursive=False)
            if len(cells) < 2:
                continue
            label = re.sub('\\s+', '', cells[0].get_text(' ', strip=True)).rstrip('：:')
            if label in ('书名', '英文名', '作者', 'ISBN', '丛书名', '关键词', '出版时间'):
                fields.append({'label': label, 'value': cells[1].get_text(' ', strip=True)})
        if any((x['label'] == '书名' and x['value'] for x in fields)):
            candidates.append(fields)
    if len(candidates) != 1 or not soup.title:
        raise RuntimeError('未识别唯一的图书书目信息')
    title = next((x['value'] for x in candidates[0] if x['label'] == '书名'))
    if not soup.title.get_text(' ', strip=True).startswith(title):
        raise RuntimeError('页面题名与书目不匹配')
    return {'source': '皮书数据库公开图书书目', 'id': book_id, 'record_url': r.url, 'fields': candidates[0], 'note': '仅网页可见的图书基本书目，不含目录、简介或全文；不证明学校已购或全文权限。'}
