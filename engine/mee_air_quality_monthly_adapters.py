"""生态环境部全国城市空气质量月报目录与 PDF 检索。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.mee.gov.cn/hjzl/dqhj/cskqzlzkyb/'

def fetch(url):
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, check=True).stdout

def list_page(page=1, keyword=''):
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('需要 Beautiful Soup 4') from e
    url = BASE + ('index.shtml' if page == 1 else f'index_{page - 1}.shtml')
    s = BeautifulSoup(fetch(url), 'html.parser')
    out = []
    for a in s.find_all('a', href=True):
        name = a.get_text(' ', strip=True)
        u = urljoin(url, a['href'])
        if re.fullmatch('\\d{4}年\\d{1,2}月全国城市空气质量报告', name) and keyword in name:
            out.append({'title': name, 'url': u})
    return {'source': url, 'page': page, 'keyword': keyword, 'items': out, 'note': '仅筛选该目录页标题，空页或无匹配不代表当期未发布。'}

def report(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.mee.gov.cn' or (not re.fullmatch('/hjzl/dqhj/cskqzlzkyb/\\d{6}/t\\d{8}_\\d+\\.shtml', u.path)) or u.query or u.fragment:
        raise ValueError('仅支持该栏目官方详情链接')
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError('需要 Beautiful Soup 4') from e
    try:
        import fitz
    except ImportError as e:
        raise RuntimeError('需要 PyMuPDF') from e
    soup = BeautifulSoup(fetch(url), 'html.parser')
    body = soup.select_one('.TRS_Editor')
    if body is None:
        raise ValueError('未识别报告详情')
    links = [urljoin(url, a['href']) for a in body.find_all('a', href=True) if a['href'].lower().endswith('.pdf')]
    if len(links) != 1:
        raise ValueError('报告PDF数量异常')
    pdf = links[0]
    p = urlsplit(pdf)
    if p.scheme != 'https' or p.netloc != 'www.mee.gov.cn' or (not re.fullmatch('/hjzl/dqhj/cskqzlzkyb/\\d{6}/W\\d+\\.pdf', p.path)):
        raise ValueError('PDF地址不符合预期')
    pages = []
    with fitz.open(stream=fetch(pdf), filetype='pdf') as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if not keyword or ''.join(keyword.split()) in ''.join(text.split()):
                pages.append({'pdf_page': i + 1, 'text': text})
    return {'source': url, 'pdf': pdf, 'keyword': keyword, 'pages': pages, 'note': '提取PDF文本；图表图片、跨列和表格结构未完整解析。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('list')
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--keyword', default='')
    a = s.add_parser('report')
    a.add_argument('url')
    a.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(list_page(a.page, a.keyword) if a.cmd == 'list' else report(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
