"""Costa Rica central bank National Summary Data Page row search."""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urljoin
from bs4 import BeautifulSoup
URL = 'https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/PAG_NAC_ING.htm'

def search(query, limit=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (not 1 <= limit <= 100):
        raise ValueError('请输入查询词，limit 应为 1–100')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', '5000000', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('哥斯达黎加央行页面请求失败: ' + p.stderr.decode('utf-8', 'replace')[:300])
    if len(p.stdout) > 5000000:
        raise ValueError('响应过大')
    soup = BeautifulSoup(p.stdout, 'html.parser')
    out = []
    total = 0
    context = []
    for tr in soup.find_all('tr'):
        cells = [re.sub('\\s+', ' ', x.get_text(' ', strip=True)).strip() for x in tr.find_all(['td', 'th']) if x.find_parent('tr') is tr]
        if not cells:
            continue
        if len(cells) < 6 and cells[0] and (len(cells[0]) < 200):
            context.append(cells)
            context = context[-4:]
        if query.casefold() not in ' '.join(cells).casefold():
            continue
        total += 1
        if len(out) < limit:
            links = [{'label': a.get_text(' ', strip=True), 'url': urljoin(URL, a['href'])} for a in tr.find_all('a', href=True)]
            out.append({'context': context.copy(), 'cells': cells, 'links': links})
    return {'source': URL, 'query': query, 'total': total, 'returned': len(out), 'rows': out, 'note': '返回官方表格原始文本；页面使用逗号作小数点。邻近 context 只是提示，不保证统计层级。应核对原表表头、脚注、观察期和责任机构；不要自动换算数值。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.query, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
