"""浙大图书馆资源访问方式与 Elsevier Scopus 官方接口；只读。"""
import release_runtime
import argparse, html, json, os, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode

class Info(HTMLParser):

    def __init__(self):
        super().__init__()
        self.row = False
        self.depth = 0
        self.parts = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div' and 'onerow' in dict(attrs).get('class', '').split() and (not self.row):
            self.row = True
            self.depth = 1
            self.parts = []
        elif self.row and tag == 'div':
            self.depth += 1

    def handle_endtag(self, tag):
        if self.row and tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.rows.append(''.join(self.parts).strip())
                self.row = False

    def handle_data(self, data):
        if self.row:
            self.parts.append(data)

def request(url, headers=None):

    def quote(v):
        if '\n' in v or '\r' in v:
            raise ValueError('请求参数不可包含换行')
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    config = 'url = ' + quote(url) + '\n'
    for name, value in (headers or {}).items():
        config += 'header = ' + quote(name + ': ' + value) + '\n'
    proc = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--location', '--max-time', '25', '--fail-with-body', '--config', '-'], input=config, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError('请求失败（curl 状态 %d）；请检查网络、授权或密钥' % proc.returncode)
    return proc.stdout

def info(resource_id):
    if not re.fullmatch('\\d{1,10}', resource_id):
        raise ValueError('资源编号必须为数字')
    url = 'https://libdb.zju.edu.cn/s/lib/libtb/show/' + resource_id
    p = Info()
    p.feed(request(url))
    rows = p.rows

    def methods(label):
        texts = [r for r in rows if r.startswith(label)]
        if not texts:
            return {'methods': [], 'status': '页面未找到对应字段'}
        text = ' '.join(texts)
        vocab = ['IP认证', 'IP登录', '学校IP控制', 'IP控制', 'WebVPN', 'CARSI', 'RVPN', '用户名/密码', '单独申请', '账号', '密码']
        return {'methods': [v for v in vocab if v.lower() in text.lower() and (not (v == 'IP控制' and '学校IP控制' in text))], 'status': '来自资源介绍页；是否可用尚需实际验证'}
    if not rows:
        raise RuntimeError('资源页面没有可解析的介绍字段，可能无此编号或页面已改版')
    return {'id': resource_id, 'source': url, 'on_campus': methods('校内访问方式：'), 'off_campus': methods('校外访问方式：'), 'general_access': methods('访问方式：'), 'note': '仅提取访问方式关键词，不包含账号密码；通用访问方式不自动推定校内或校外可用，机构 IP 认证与接口密钥是不同机制。'}

def scopus(query, count):
    key = release_runtime.environment.get('ELSEVIER_API_KEY', '')
    if not key:
        raise ValueError('需要设置 ELSEVIER_API_KEY；馆藏 IP 认证不等于 API 密钥')
    if not 1 <= count <= 10:
        raise ValueError('每次 1–10 条')
    headers = {'Accept': 'application/json', 'X-ELS-APIKey': key}
    token = release_runtime.environment.get('ELSEVIER_INSTTOKEN', '')
    if token:
        headers['X-ELS-Insttoken'] = token
    url = 'https://api.elsevier.com/content/search/scopus?' + urlencode({'query': query, 'count': count, 'start': 0})
    try:
        return json.loads(request(url, headers))
    except json.JSONDecodeError:
        raise RuntimeError('上游返回非 JSON，可能改版或要求其他授权')

def main():
    parser = argparse.ArgumentParser(description='浙大馆藏只读接口')
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('info')
    p.add_argument('id', help='图书馆导航资源编号')
    p = sub.add_parser('scopus-search')
    p.add_argument('query')
    p.add_argument('--count', type=int, default=5)
    args = parser.parse_args()
    result = info(args.id) if args.cmd == 'info' else scopus(args.query, args.count)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
