"""国家疾病预防控制局疫情信息公开列表及概况。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
BASE = 'https://www.ndcpa.gov.cn'
INDEX = BASE + '/jbkzzx/c100016/common/list.html'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'detailContent':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def ndcpa_epidemic_list(keyword=''):
    text = fetch(INDEX)
    m = re.search('var\\s+itemObj\\s*=\\s*(\\[.*?\\]);', text, re.S)
    if not m:
        raise ValueError('未识别疫情列表')
    data = json.loads(m.group(1))
    items = []
    for row in data:
        title = row.get('aT', '')
        id = str(row.get('id', ''))
        links = json.loads(row.get('aU', '{}'))
        path = links.get('common', '')
        if keyword in title and re.fullmatch('/jbkzzx/c100016/common/content/content_\\d+\\.html', path) and path.endswith('_' + id + '.html'):
            items.append({'id': id, 'title': title, 'published': row.get('aPd'), 'path': path, 'url': BASE + path})
    return {'source': '国家疾病预防控制局疫情信息', 'source_url': INDEX, 'items': items, 'note': '仅当前页面列出的疫情信息标题，不是病例级数据或全部历史。'}

def ndcpa_epidemic_detail(identifier):
    if not re.fullmatch('\\d+', str(identifier)):
        raise ValueError('编号应为数字')
    matches = [i for i in ndcpa_epidemic_list()['items'] if i['id'] == str(identifier)]
    if not matches:
        raise ValueError('编号不在当前列表')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别疫情概况正文')
    return {'source': '国家疾病预防控制局疫情信息', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '保留官网正文和注释，表格文字行列可能错位。网络直报死亡数据不能作为我国传染病死因顺位依据，请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(ndcpa_epidemic_list(a.keyword) if a.cmd == 'list' else ndcpa_epidemic_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
