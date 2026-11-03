"""地震科学国际数据中心公开网站搜索；结果为网站内容条目。"""
import release_runtime
import html
import json
import re
import subprocess
from urllib.parse import urlencode, urljoin
BASE = 'https://www.esdc.ac.cn'

def search(keyword, page=1):
    if not keyword.strip() or not 1 <= int(page) <= 10000:
        raise ValueError('请提供关键词及正整数页码')
    url = BASE + '/search?' + urlencode({'keyword': keyword, 'page': page})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('地震科学国际数据中心请求失败: ' + p.stderr.strip())
    if 'class="searchList"' not in p.stdout:
        raise RuntimeError('响应不是预期搜索结果，站点可能已变化')
    body = p.stdout.split('class="searchList"', 1)[1].split('</ul>', 1)[0]
    items = []
    for href, title in re.findall('<a\\s+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
        if not re.fullmatch('https://www\\.esdc\\.ac\\.cn/(?:article|class)/\\d+', href):
            continue
        title = html.unescape(re.sub('<[^>]*>', '', title)).strip()
        items.append({'title_as_displayed': title, 'url': urljoin(BASE, href), 'type': 'article' if '/article/' in href else 'category'})
    next_match = re.search('<a class="next" href="([^"]+)"', p.stdout)
    has_next = bool(next_match and next_match.group(1).startswith('/search?'))
    return {'source': '地震科学国际数据中心网站搜索', 'keyword': keyword, 'page': int(page), 'has_next': has_next, 'items': items}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyword')
    parser.add_argument('--page', type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.page), ensure_ascii=False, indent=2))
