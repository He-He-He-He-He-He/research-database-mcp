"""爱学术匿名书目详情；不提供试读、附件或全文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
_BAD = re.compile('(?:https?://|www\\.|(?:token|session|csrf|api[_-]?key)\\s*=)', re.I)

def _safe(value):
    return value if isinstance(value, str) and (not _BAD.search(value)) else None

def detail(book_id):
    if not isinstance(book_id, str) or not re.fullmatch('[0-9a-f]{32}', book_id):
        raise ValueError('书号须为32位小写十六进制')
    try:
        r = requests.get('https://www.iresearchbook.cn/f/ebook/detail', params={'id': book_id}, timeout=20)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError('爱学术公开详情请求失败') from exc
    if len(r.content) > 5000000:
        raise RuntimeError('书目响应过大')
    soup = BeautifulSoup(r.content, 'html.parser')
    if not re.search('\\bbookId\\s*=\\s*[\'\\"]' + re.escape(book_id) + '[\'\\"]', r.text):
        raise ValueError('书号不存在或站方未回显')
    card = soup.select_one('.ebook-detail-content')
    title = card.select_one('.title') if card else None
    name = _safe(title.get_text(' ', strip=True) if title else None)
    if not name:
        raise ValueError('书目详情缺少题名')
    sub = card.select_one('.subtitle')
    fields = []
    omitted = []
    for label in card.select('.intro-lable'):
        parent = label.parent
        if 'sourceLi' in (parent.get('class') or []):
            continue
        key = label.get_text(' ', strip=True).strip(' ：:')
        full = parent.get_text(' ', strip=True)
        prefix = label.get_text(' ', strip=True)
        value = full[len(prefix):].strip() if full.startswith(prefix) else ''
        if not key:
            continue
        value = _safe(value)
        if value is None:
            omitted.append(key)
        else:
            fields.append({'label': key, 'value': value})
    summary = None
    for h in soup.select('.header'):
        if h.get_text(' ', strip=True) == '内容简介':
            box = h.find_next_sibling('div', class_='content-intro')
            if box:
                text = box.get_text(' ', strip=True)
                summary = _safe(text)
                if summary is None:
                    omitted.append('内容简介')
            break
    out = {'id': book_id, 'title': name, 'subtitle': _safe(sub.get_text(' ', strip=True) if sub else None), 'fields': fields, 'summary': summary}
    if omitted:
        out['source_fields_omitted'] = omitted
    return {'source': '爱学术公开书目详情', 'record': out, 'note': '匿名公开题录与简介，未验证浙江大学已购、试读或全文权限。'}
