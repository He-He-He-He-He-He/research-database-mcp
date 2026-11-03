"""万方医学网公开论文检索，读取网页结果的题录链接。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from research import fetch

class Results(HTMLParser):

    def __init__(self):
        super().__init__()
        self.capture = None
        self.title = []
        self.count_text = []
        self.counting = False
        self.items = []
        self.saw_count = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'span' and 'mod-results-count' in a.get('class', '').split():
            self.counting = True
            self.saw_count = True
        if tag == 'a' and a.get('data-logname') == 'searchResultTitleLink':
            url = a.get('href', '')
            parts = urlparse(url)
            if parts.scheme == 'https' and parts.netloc == 'med.wanfangdata.com.cn' and (parts.path == '/Paper/Detail'):
                self.capture = url
                self.title = []

    def handle_data(self, data):
        if self.counting:
            self.count_text.append(data)
        if self.capture:
            self.title.append(data)

    def handle_endtag(self, tag):
        if tag == 'span' and self.counting:
            self.counting = False
        if tag == 'a' and self.capture:
            self.items.append({'title': ' '.join(''.join(self.title).split()), 'url': self.capture})
            self.capture = None

def search(keyword, page=1):
    keyword = keyword.strip()
    if not keyword or len(keyword) > 100 or re.search('[()\\x00-\\x1f]', keyword):
        raise ValueError('关键词需为 1–100 字，不支持括号或控制字符')
    if not 1 <= page <= 100:
        raise ValueError('page 必须为 1–100')
    url = 'https://med.wanfangdata.com.cn/Paper/Search?' + urlencode({'q': '关键词=(' + keyword + ')', 'p': page})
    raw = fetch(url)
    if '人机校验' in raw or '&#x4EBA;&#x673A;&#x6821;&#x9A8C;' in raw:
        raise RuntimeError('万方医学网要求人机校验，请在网站正常完成验证后使用；程序不会绕过')
    p = Results()
    p.feed(raw)
    if not p.saw_count:
        raise RuntimeError('未找到结果计数，页面可能要求登录、验证或结构已变化')
    count = re.search('共\\s*([\\d,]+)\\s*条', ''.join(p.count_text))
    if not count:
        raise RuntimeError('无法解析结果数')
    return {'source': '万方医学网', 'search_url': url, 'query': keyword, 'page': page, 'total': int(count.group(1).replace(',', '')), 'items': p.items, 'note': '仅页面中的题名与详情链接；医学网覆盖范围、全文权限和浙大机构识别尚未验证。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
