"""CNNIC 历次互联网统计基础数据目录和官方图表。"""
import release_runtime
import hashlib, re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.cnnic.cn'
INDEX = BASE + '/6/132/'

def _get(url, cap=5000000):
    with requests.get(url, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源发生重定向')
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > cap:
                raise ValueError('来源超过大小上限')
        return bytes(buf)

def catalog():
    u = INDEX + 'index.html'
    s = BeautifulSoup(_get(u), 'html.parser')
    items = []
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})/(\\d{1,2})\\s*第(\\d+)次统计报告基础数据', title)
        url = urljoin(u, a['href'])
        p = urlsplit(url)
        if m and 1 <= int(m[2]) <= 12 and (p.scheme == 'https') and (p.hostname == 'www.cnnic.cn') and re.fullmatch('/n4/\\d{4}/\\d{4}/c132-\\d+\\.html', p.path):
            items.append({'issue': int(m[3]), 'label_year': int(m[1]), 'label_month': int(m[2]), 'title': title, 'url': url})
    return {'source': '中国互联网络信息中心统计报告基础数据', 'source_url': u, 'items': items, 'note': '时间标签按官方目录原文提供，调查截止时间须核对报告；数据为图像基础指标，并非实时用户数据。'}

def detail(issue):
    if isinstance(issue, bool) or not isinstance(issue, int) or (not 1 <= issue <= 999):
        raise ValueError('issue 须为 1–999')
    item = next((x for x in catalog()['items'] if x['issue'] == issue), None)
    if not item:
        raise ValueError('首页目录未找到该期')
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    body = soup.select_one('.inner-text')
    if not body:
        raise ValueError('未识别正文')
    images = []
    for img in body.select('img[src]'):
        url = urljoin(item['url'], img['src'])
        p = urlsplit(url)
        if p.scheme == 'https' and p.hostname == 'www.cnnic.cn' and p.path.startswith('/NMediaFile/') and p.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            raw = _get(url)
            if not (raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'\xff\xd8\xff') or raw.startswith((b'GIF87a', b'GIF89a'))):
                raise ValueError('图像类型不匹配')
            images.append({'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'image_bytes': raw})
    if not images:
        raise ValueError('未识别官方图像')
    return {'source': '中国互联网络信息中心统计报告基础数据', **item, 'images': images, 'note': '返回官方图表原始图像，image_bytes 为 Python bytes，未 OCR、未自动解析数值；需核原报告调查时间、定义和统计方法。'}
