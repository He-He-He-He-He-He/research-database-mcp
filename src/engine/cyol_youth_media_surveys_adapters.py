"""中国青年报·中青校媒发布的大学生社交媒体调查报道。"""
import release_runtime
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).parent
SOURCES = {2025: ('中青校媒大学生网络空间调查2025.html', 'https://zqb.cyol.com/pc/content/202512/22/content_420243.html'), 2026: ('中青校媒大学生虚假信息调查2026.html', 'https://zqb.cyol.com/pc/content/202608/21/content_429703.html')}

class _Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.in_p = False
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag == 'p':
                self.in_p = True
                self.parts = []
        elif tag == 'div' and dict(attrs).get('id') == 'content':
            self.depth = 1

    def handle_data(self, data):
        if self.depth and self.in_p:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'p' and self.in_p:
            t = ' '.join(''.join(self.parts).split())
            if t:
                self.paragraphs.append(t)
            self.in_p = False
        if tag == 'div':
            self.depth -= 1

def search_youth_media_surveys(year, keyword=''):
    """检索两个不同调查的新闻正文，year 为报道发布年份。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2025 或 2026')
    filename, url = SOURCES[year]
    p = _Paragraphs()
    p.feed((ROOT / filename).read_text(encoding='utf-8'))
    if not p.paragraphs:
        raise ValueError('调查报道正文解析失败')
    keyword = keyword.strip()
    return [{'publication_year': year, 'paragraph': i, 'text': t, 'source_url': url, 'source_type': '调查机构的新闻报道'} for i, t in enumerate(p.paragraphs, 1) if not keyword or keyword in t]
