"""全唐诗 / 全宋诗试用库：仅读取诗题和作者题录。"""
import release_runtime
import argparse, json, re
from urllib.request import urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup
BASE = 'http://www.chinabooktrading.com/'

def detail(kind, poem_id):
    if kind not in ('song', 'tang'):
        raise ValueError('类型必须是 song 或 tang')
    if isinstance(poem_id, bool) or not isinstance(poem_id, int) or (not 1 <= poem_id <= 9999999):
        raise ValueError('作品 ID 须为正整数')
    url = BASE + kind + '/fullText.jsp?' + urlencode({'a': '1', 'e': '1' if kind == 'song' else '0', 'u': poem_id, 'b': '4'})
    with urlopen(url, timeout=20) as r:
        html = r.read().decode('utf-8', 'replace')
    s = BeautifulSoup(html, 'html.parser')
    head = s.select_one('h2.nametitle')
    h3 = head.find_next('h3') if head else None
    h4 = h3.find_next('h4') if h3 else None
    expected = '詩:宋詩' if kind == 'song' else '詩:唐詩'
    if not head or not head.get_text(' ', strip=True).startswith(expected) or (not h3) or (not h4):
        raise RuntimeError('未识别作品题录；可能作品不存在或试用权限有限')
    title = h3.get_text(' ', strip=True)
    author = h4.get_text(' ', strip=True)
    if not title or not author:
        raise RuntimeError('作品题名或作者缺失')
    return {'source': '全宋诗分析系统' if kind == 'song' else '全唐诗分析系统', 'scope': '试用库仅含部分作品', 'id': poem_id, 'title': title, 'author': author, 'record_url': url, 'note': '只返回标题及作者，未提取正文或注释；上游 HTTP 明文，公开检索不证明机构全文权限。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('kind', choices=['song', 'tang'])
    p.add_argument('id', type=int)
    a = p.parse_args()
    print(json.dumps(detail(a.kind, a.id), ensure_ascii=False, indent=2))
