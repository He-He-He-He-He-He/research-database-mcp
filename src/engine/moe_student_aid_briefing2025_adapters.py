"""教育部 2026 年学生资助发布会公开实录检索。"""
import release_runtime
from html.parser import HTMLParser
from pathlib import Path
HTML_PATH = Path(__file__).with_name('2025年度学生资助新闻发布会实录.html')
SOURCE_URL = 'https://www.moe.gov.cn/fbh/live/2026/78343/twwd/202607/t20260728_1445368.html'

class _Segments(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.segments = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == 'div':
                self.depth += 1
        elif tag == 'div' and 'twzb_content' in dict(attrs).get('class', '').split():
            self.depth = 1
            self.parts = []

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1
            if not self.depth:
                t = ' '.join(''.join(self.parts).split())
                if t:
                    self.segments.append(t)

def search_student_aid_briefing2025(keyword=''):
    """按发布会实录原文段落搜索，保留政策、时间和单位。"""
    p = _Segments()
    p.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(p.segments) < 50:
        raise ValueError('发布会实录解析异常')
    keyword = keyword.strip()
    return [{'segment': i, 'text': t, 'source_url': SOURCE_URL, 'publication_year': 2026, 'source_type': '新闻发布会实录'} for i, t in enumerate(p.segments, 1) if not keyword or keyword in t]
