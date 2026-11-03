"""国家医保局医保数智库公开数据专题。"""
import release_runtime
import argparse, html, json, re, sys
from urllib.parse import urljoin, urlsplit
from nhsa_statistics_adapters import fetch, Body, BASE
INDEX = BASE + '/col/col257/'

def nhsa_databank_list(keyword=''):
    pairs = re.findall('<a\\s+href="(/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_257_\\d+\\.html)"\\s+title="([^"]+)"', fetch(INDEX))
    if not pairs:
        raise ValueError('未识别医保数智库列表')
    seen = set()
    items = []
    for path, title in pairs:
        title = html.unescape(title)
        if path not in seen and keyword in title:
            items.append({'path': path, 'title': title, 'url': BASE + path})
            seen.add(path)
    return {'source': '国家医疗保障局医保数智库', 'source_url': INDEX, 'items': items, 'note': '仅当前栏目首页标题；不是个人账户或全部医保统计。'}

def nhsa_databank_detail(path):
    matches = [i for i in nhsa_databank_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    images = []
    for i in p.images:
        u = urljoin(url, i)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.nhsa.gov.cn':
            images.append(u)
    if not p.title or not (text or images):
        raise ValueError('未识别医保数智库正文')
    return {'source': '国家医疗保障局医保数智库', 'title': p.title, 'url': url, 'text': text, 'images': images, 'note': '数据可能仅在图片中，未 OCR；统计来源、说明与可比性请核对官方页面。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(nhsa_databank_list(a.keyword) if a.cmd == 'list' else nhsa_databank_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
