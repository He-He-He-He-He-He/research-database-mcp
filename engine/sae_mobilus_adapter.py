"""SAE Mobilus 公共搜索首屏目录的本地筛选，不调用机构授权内容。"""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
URL = 'https://saemobilus.sae.org/search'

def catalog_page(keyword: str='') -> dict:
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    r = requests.get(URL, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    cards = soup.select('a[href] > span > mat-card.si-card--content')
    if not cards:
        raise RuntimeError('未识别到 SAE Mobilus 目录，可能遇到验证或页面改版')
    records = []
    for card in cards:
        a = card.find_parent('a', href=True)
        title = card.select_one('mat-card-title')
        code = card.select_one('.si-prod-code')
        date = card.select_one('.si-date')
        if not a or not title:
            continue
        title_text = title.get_text(' ', strip=True)
        code_text = code.get_text(' ', strip=True) if code else ''
        if keyword and keyword.casefold() not in (title_text + ' ' + code_text).casefold():
            continue
        records.append({'title': title_text, 'code': code_text or None, 'date': date.get_text(' ', strip=True) if date else None, 'url': urljoin(URL, a['href']), 'restricted': bool(card.select_one('[aria-label="Document Locked"]'))})
    return {'source': 'SAE Mobilus 公开目录', 'keyword': keyword, 'items': records, 'scope': f'仅筛选未登录公开首页 {len(cards)} 条，不是全库搜索；不代表机构全文权限', 'license_note': '学校和供应商对自动读取的适用许可尚未核实', 'library_entry': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1295'}
