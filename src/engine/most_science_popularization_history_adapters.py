"""科技部 2023 和 2024 年度科普统计发布原文。"""
import release_runtime
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).parent
SOURCES = {2023: 'https://www.most.gov.cn/kjbgz/202412/t20241230_192807.html', 2024: 'https://www.most.gov.cn/kjbgz/202601/t20260127_195796.html'}

class _Content(HTMLParser):

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
        elif tag == 'div' and {'trs_editor_view', 'trs_editor'} & set(dict(attrs).get('class', '').lower().split()):
            self.depth = 1

    def handle_data(self, data):
        if self.depth and self.in_p:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'p' and self.in_p:
            text = ' '.join(''.join(self.parts).split())
            if text:
                self.paragraphs.append(text)
            self.in_p = False
        if tag == 'div':
            self.depth -= 1

def search_science_popularization_history(year, keyword=''):
    """查询 2023、2024 年科技部发布段落。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2023 或 2024')
    parser = _Content()
    parser.feed((ROOT / f'科技部{year}年度全国科普统计数据.html').read_text(encoding='utf-8'))
    if len(parser.paragraphs) < 5:
        raise ValueError('科普统计正文解析异常')
    keyword = keyword.strip()
    return [{'reference_year': year, 'publication_year': 2024 if year == 2023 else 2026, 'paragraph': i, 'text': t, 'source_url': SOURCES[year]} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
