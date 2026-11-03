"""浙大文库公开动态正文；仅处理文库站内 news/detail。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
BASE = 'http://csid.zju.edu.cn/zjuwk/news/detail'

def detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('动态编号须为 32 位十六进制')
    record_id = record_id.lower()
    url = BASE + '?' + urlencode({'id': record_id})
    with urlopen(url, timeout=20) as response:
        html = response.read(2000001)
    if len(html) > 2000000:
        raise RuntimeError('页面超过大小上限')
    soup = BeautifulSoup(html, 'html.parser')
    detail_node = soup.select_one('.news-detail')
    title = detail_node.select_one('h2.news-title') if detail_node else None
    body = detail_node.select_one('.news-main') if detail_node else None
    if not title or not title.get_text(strip=True) or (not body):
        raise RuntimeError('未识别动态正文，页面可能发生变化')
    date = next((s.get_text(' ', strip=True).removeprefix('日期：') for s in detail_node.find_all('span', recursive=False) if s.get_text(strip=True).startswith('日期：')), None)
    paragraphs = [p.get_text('', strip=True) for p in body.find_all('p')]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        raise RuntimeError('未识别正文段落')
    return {'source': '浙大文库动态', 'record_url': url, 'title': title.get_text(' ', strip=True), 'date': date, 'paragraphs': paragraphs, 'note': '仅公开动态页面；图片、附件及格式未读取，正文可能更新；上游 HTTP，勿传敏感信息。'}
