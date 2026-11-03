"""Search Egypt planning ministry NSDP table; return original cells and context."""
import release_runtime
import argparse, json, re, time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
URL = 'https://mped.gov.eg/assets/uploads/NSDP.html'

def search(query, limit=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (not 1 <= limit <= 100):
        raise ValueError('请输入查询词，limit 应在 1–100')
    s = requests.Session()
    s.trust_env = False
    for attempt in range(3):
        try:
            r = s.get(URL, timeout=30)
            r.raise_for_status()
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    if len(r.content) > 5000000:
        raise ValueError('响应超过大小上限')
    soup = BeautifulSoup(r.content, 'html.parser')
    out = []
    total = 0
    context = []
    for tr in soup.find_all('tr'):
        cells = [re.sub('\\s+', ' ', x.get_text(' ', strip=True)).strip() for x in tr.find_all(['td', 'th']) if x.find_parent('tr') is tr]
        if not cells:
            continue
        if len(cells) < 6 and cells[0] and (len(cells[0]) < 240):
            context.append(cells)
            context = context[-4:]
        if query.casefold() not in ' '.join(cells).casefold():
            continue
        total += 1
        if len(out) < limit:
            links = [{'text': a.get_text(' ', strip=True), 'url': urljoin(URL, a['href'])} for a in tr.find_all('a', href=True)]
            out.append({'context': context.copy(), 'cells': cells, 'links': links})
    return {'source': URL, 'query': query, 'total': total, 'returned': len(out), 'rows': out, 'note': '页面表格行与前置短行原样提取，context 是邻近文本不是可靠的层级或责任机构；必须回原页及脚注核对口径、观察期和来源，不要根据页面更新日期代替单项时点。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
