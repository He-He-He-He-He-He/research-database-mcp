"""广播电视总局历年广播电视行业统计公报本地原文段落查询。"""
import release_runtime
from html.parser import HTMLParser
from pathlib import Path
import re
ROOT = Path(__file__).parent
SOURCES = {2025: 'https://www.nrta.gov.cn/art/2026/5/13/art_113_73265.html', 2024: 'https://www.nrta.gov.cn/art/2025/5/9/art_113_70729.html', 2023: 'https://www.nrta.gov.cn/art/2024/5/8/art_113_67383.html'}

class _Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.in_p = False
        self.chunks = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag == 'p':
                self.in_p = True
                self.chunks = []
        elif tag == 'div' and dict(attrs).get('id') == 'zoom':
            self.depth = 1

    def handle_data(self, data):
        if self.depth and self.in_p:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'p' and self.in_p:
            t = ' '.join(''.join(self.chunks).split())
            if t:
                self.paragraphs.append(t)
            self.in_p = False
        if tag == 'div':
            self.depth -= 1

def search_broadcast_statistics(year, keyword=''):
    """在 2023—2025 年公报中按原文段落匹配，保留全部脚注。"""
    if year not in SOURCES:
        raise ValueError('支持 2023、2024、2025')
    parser = _Paragraphs()
    parser.feed((ROOT / f'{year}年全国广播电视行业统计公报.html').read_text(encoding='utf-8'))
    if not parser.paragraphs:
        raise ValueError('统计公报正文未识别到段落')
    notes = [p for p in parser.paragraphs if re.match('^\\[\\d+\\]', p)]
    keyword = keyword.strip()
    rows = [{'paragraph': i, 'text': text, 'source_url': SOURCES[year], 'reference_year': year} for i, text in enumerate(parser.paragraphs, 1) if not keyword or keyword in text]
    return {'reference_year': year, 'publication_year': year + 1, 'source_url': SOURCES[year], 'results': rows, 'footnotes': notes}
