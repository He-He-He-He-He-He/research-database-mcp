"""北京市统计局工业月度原表目录和 XLS 读取。"""
import release_runtime
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from html.parser import HTMLParser
from research import fetch
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import xlrd
BASE = 'https://tjj.beijing.gov.cn/tjsj_31433/yjdsj_31440/gy_31782/'

def index(year=2026, keyword=''):
    if not 2010 <= year <= 2100:
        raise ValueError('年份须在 2010 至 2100')
    url = BASE + str(year) + '/'
    page = fetch(url)
    items = []
    pattern = '<td\\s+colspan="4"[^>]*>([^<]+)</td>\\s*<script[^>]*>.*?title\\s*=\\s*"([^"]*)";\\s*link\\s*=\\s*"([^"]*)";'
    for title, dates, links in re.findall(pattern, page, re.S):
        dates = [v for v in dates.split(';') if v]
        links = [v for v in links.split(';') if v]
        if len(dates) != len(links):
            raise ValueError('目录日期与链接数量不匹配')
        for period, link in zip(dates, links):
            if keyword in title:
                items.append({'table': title.strip(), 'period_label': period, 'url': urljoin(url, link)})
    if not re.search(pattern, page, re.S):
        raise ValueError('未能解析目录，年份可能未发布或网页改版')
    return {'source': url, 'year': year, 'items': items, 'scope': '当前年度工业月度目录标题过滤；期次标签以官网为准'}

class Attach(HTMLParser):

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.items = []

    def handle_starttag(self, t, attrs):
        if t == 'a':
            u = urljoin(self.url, dict(attrs).get('href', ''))
            v = urlsplit(u)
            if v.scheme == 'https' and v.netloc == 'tjj.beijing.gov.cn' and v.path.lower().endswith('.xls') and (not v.query) and (not v.fragment):
                self.items.append(u)

def detail(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'tjj.beijing.gov.cn' or (not re.fullmatch('/tjsj_31433/yjdsj_31440/gy_31782/\\d{4}/\\d{6}/t\\d+_\\d+\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('仅支持目录返回的工业统计页面')
    p = Attach(url)
    p.feed(fetch(url))
    links = list(dict.fromkeys(p.items))
    if len(links) != 1:
        raise ValueError('未找到唯一 XLS 附件，网站可能改版')
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', '--max-filesize', '5242880', links[0]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = result.stdout
    if not data.startswith(bytes.fromhex('d0cf11e0a1b11ae1')) or len(data) > 5242880:
        raise ValueError('附件不是预期 XLS 文件')
    b = xlrd.open_workbook(file_contents=data, formatting_info=True)
    sheets = []
    for s in b.sheets():
        if s.nrows > 1000 or s.ncols > 100:
            raise ValueError('表格超出读取上限')
        sheets.append({'name': s.name, 'rows': [[s.cell_value(r, c) for c in range(s.ncols)] for r in range(s.nrows)], 'merged_ranges': s.merged_cells})
    return {'source': url, 'attachment': links[0], 'sha256': hashlib.sha256(data).hexdigest(), 'sheets': sheets, 'note': '原表单元格和合并范围；空白不表示零，单位及统计口径以表内说明为准'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--year', type=int, default=2026)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(index(a.year, a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
