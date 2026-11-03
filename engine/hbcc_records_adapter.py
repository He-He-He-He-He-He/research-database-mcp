"""Navigate selected groups to visible records in the Chinese historical bibliography."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit, parse_qs, urlencode
import requests
from bs4 import BeautifulSoup
BASE = 'http://www.chinabooktrading.com/hbcc/'
GROUP = re.compile('^(.*?)\\s*\\(包含\\s*(\\d+)\\s*個子分組\\s*(\\d+)\\s*條書目\\)\\s*$')

def records(keyword, group_path, limit=10, session=None):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '[]!')) or (not isinstance(group_path, list)) or (not 0 <= len(group_path) <= 5) or any((not isinstance(x, str) or not x.strip() or len(x) > 150 for x in group_path)) or (type(limit) is not int) or (not 1 <= limit <= 20):
        raise ValueError('需要关键词、最多 5 层准确分组和 1–20 条上限')
    q = keyword.strip()
    sess = session or requests.Session()
    r = sess.get(BASE + 'search/search.action', params={'query': f'[ft:{q}]!3', 'orderField': 'order0'}, timeout=20)
    r.raise_for_status()

    def parse(r):
        r.encoding = 'utf-8'
        s = BeautifulSoup(r.text, 'html.parser')
        text = s.get_text(' ', strip=True)
        if f'全文:{q};' not in text:
            raise ValueError('上游检索词不匹配')
        return s
    soup = parse(r)
    for component in group_path:
        matches = []
        for a in soup.select('a.list'):
            m = GROUP.fullmatch(a.get_text(' ', strip=True))
            href = a.get('href', '')
            if m and m.group(1).strip() == component.strip() and href.startswith('search/search.action?'):
                matches.append(href)
        if len(matches) != 1:
            raise ValueError('分组不存在或不唯一，请核对路径')
        url = urljoin(BASE, matches[0])
        u = urlsplit(url)
        if u.hostname != 'www.chinabooktrading.com' or u.path != '/hbcc/search/search.action':
            raise ValueError('分组链接异常')
        r = sess.get(url, timeout=20)
        r.raise_for_status()
        soup = parse(r)
    items = []
    groups = []
    for a in soup.select('a.list'):
        href = a.get('href', '')
        text = a.get_text(' ', strip=True)
        match = GROUP.fullmatch(text)
        if match and href.startswith('search/search.action?'):
            groups.append({'name': match.group(1).strip(), 'subgroups': int(match.group(2)), 'records': int(match.group(3))})
            continue
        if not href.startswith('browse/browseBook.action?') or not text:
            continue
        u = urlsplit(urljoin(BASE, href))
        entry = parse_qs(u.query).get('entryId', [])
        if u.hostname != 'www.chinabooktrading.com' or u.path != '/hbcc/browse/browseBook.action' or len(entry) != 1 or (not entry[0].isdigit()):
            continue
        items.append({'title': text, 'entry_id': entry[0]})
    if not items and (not groups):
        raise ValueError('没有可识别书目或分组，空结果未验证')
    return {'source': '中国历代典籍总目', 'query': q, 'group_path': group_path, 'groups': groups[:limit], 'items': items[:limit], 'returned_groups': min(len(groups), limit), 'returned_items': min(len(items), limit), 'note': '当前可见分组或书目，不代表全库或全文；HTTP 明文，请勿使用敏感关键词。'}
