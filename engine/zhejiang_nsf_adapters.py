"""浙江省自然科学基金委员会官网公开通知与基金工作。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode
BASE = 'https://zjnsf.kjt.zj.gov.cn'
CATEGORIES = {'notice': ('通知通告', '2018515'), 'work': ('基金工作', '1003')}

def fetch(url):
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('浙江省自然科学基金网站请求失败: ' + p.stderr.strip())
    return p.stdout

def search(keyword='', category='notice', page=1, size=10):
    if category not in CATEGORIES or not 1 <= int(page) <= 10000 or (not 1 <= int(size) <= 50):
        raise ValueError('栏目、页码或每页条数不合法')
    label, cid = CATEGORIES[category]
    params = {'categoryId': cid, 'paging': 1, 'page_size': int(size), 'page_index': int(page)}
    try:
        d = json.loads(fetch(BASE + '/insiis7/api/site/post/list?' + urlencode(params)))
        if d.get('success') is not True or not isinstance(d.get('body'), list) or int(d['page']) != int(page):
            raise ValueError('列表状态或页码异常')
        items = []
        for row in d['body']:
            pid = str(row['postId'])
            title = re.sub('<br\\s*/?>', ' ', str(row['title']), flags=re.I).strip()
            if not pid.isdigit() or not title or str(row['categoryId']) != cid:
                raise ValueError('列表数据不完整或栏目不匹配')
            if keyword in title:
                items.append({'id': pid, 'title': title, 'published': row.get('publishTime'), 'source': row.get('source'), 'url': BASE + '/insiis7/api/site/v1/post/detail?' + urlencode({'categoryId': cid, 'postId': pid})})
        total = int(d['total'])
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError('基金网站列表结构异常，未返回部分结果') from exc
    return {'source': '浙江省自然科学基金委员会', 'category': label, 'page': int(page), 'page_size': int(size), 'total': total, 'keyword': keyword, 'page_items': len(d['body']), 'items': items, 'scope': '按指定栏目当前页标题筛选；total 为该栏目总量而非关键词命中数。项目申报和立项结果不在本接口范围。'}

def search_all(keyword='', category='notice', limit=50, offset=0):
    if category not in CATEGORIES or not isinstance(keyword, str):
        raise ValueError('栏目或关键词无效')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为 1–100，offset 须为 0–100000')
    first = search('', category, 1, 50)
    total = first['total']
    if total < 0 or total > 1000:
        raise RuntimeError('栏目总数超出本次 20 页安全上限或无效')
    pages = max(1, (total + 49) // 50)
    all_items = []
    ids = set()
    for n in range(1, pages + 1):
        r = first if n == 1 else search('', category, n, 50)
        if r['total'] != total or r['page_items'] != len(r['items']) or r['page_items'] != min(50, max(0, total - (n - 1) * 50)):
            raise RuntimeError('栏目总数或页大小变化，无法确认遍历范围')
        for item in r['items']:
            if item['id'] in ids:
                raise RuntimeError('跨页存在重复编号，栏目可能发生变化')
            ids.add(item['id'])
            all_items.append(item)
    matches = [item for item in all_items if keyword in item['title']]
    selected = matches[offset:offset + limit]
    return {'source': '浙江省自然科学基金委员会', 'category': CATEGORIES[category][0], 'keyword': keyword, 'upstream_total': total, 'source_pages': pages, 'matched_count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(matches) else None, 'items': selected, 'scope': '逐页读取所选栏目并按标题本地筛选；目录可能变化，跨页不是原子快照，本地偏移可能随更新变化。项目申报和立项结果不在本接口范围。'}

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = ''
        self.date = ''
        self.depth = 0
        self.text = []
        self.skip = 0
        self.seen = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'meta' and a.get('name') == 'PubDate':
            self.date = a.get('content', '')
        if self.depth:
            if t in ('script', 'style'):
                self.skip += 1
            if t not in ('br', 'img', 'hr', 'meta', 'input', 'link', 'source', 'wbr'):
                self.depth += 1
            if t in ('p', 'div', 'tr', 'li', 'br'):
                self.text.append('\n')
        elif t == 'div' and a.get('id') == 'info' and ('con-article' in a.get('class', '').split()):
            self.depth = 1
            self.seen = True

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.text.append(s)

    def handle_endtag(self, t):
        if not self.depth:
            return
        if t in ('script', 'style') and self.skip:
            self.skip -= 1
        if t not in ('br', 'img', 'hr', 'meta', 'input', 'link', 'source', 'wbr'):
            self.depth -= 1
        if t in ('p', 'div', 'tr', 'li'):
            self.text.append('\n')

def detail(post_id, category='notice'):
    if category not in CATEGORIES or not str(post_id).isdigit():
        raise ValueError('请提供正确栏目和数字 post_id')
    label, cid = CATEGORIES[category]
    url = BASE + '/insiis7/api/site/v1/post/detail?' + urlencode({'categoryId': cid, 'postId': str(post_id)})
    p = Article()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.text).splitlines() if x.strip()))
    if not p.title or not p.seen or (not text):
        raise RuntimeError('基金通知正文缺失或网站结构变化')
    return {'source': '浙江省自然科学基金委员会', 'category': label, 'id': str(post_id), 'title': p.title, 'published': p.date, 'text': text, 'url': url, 'note': '官网正文文本；附件不包含在内，实际要求和最新状态请核对原站。'}
if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument('keyword', nargs='?', default='')
    a.add_argument('--category', choices=CATEGORIES, default='notice')
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--size', type=int, default=10)
    a.add_argument('--detail')
    o = a.parse_args()
    print(json.dumps(detail(o.detail, o.category) if o.detail else search(o.keyword, o.category, o.page, o.size), ensure_ascii=False, indent=2))
