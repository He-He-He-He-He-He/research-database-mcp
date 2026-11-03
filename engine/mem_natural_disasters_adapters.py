"""应急管理部公开全国自然灾害通报：固定来源目录和原文段落查询。"""
import release_runtime
import argparse, json, re, subprocess
from html.parser import HTMLParser
REPORTS = {'2024': ('2024年全年', 'https://www.mem.gov.cn/xw/yjglbgzdt/202501/t20250117_516032.shtml'), '2025': ('2025年全年', 'https://www.mem.gov.cn/xw/yjglbgzdt/202601/t20260116_592135.shtml'), '2026-h1': ('2026年上半年', 'https://www.mem.gov.cn/xw/yjglbgzdt/202607/t20260713_676243.shtml'), '2026-q1-q3': ('2026年前三季度', 'https://www.mem.gov.cn/xw/yjglbgzdt/202610/t20261022_736602.shtml'), '2026-07': ('2026年7月', 'https://www.mem.gov.cn/xw/yjglbgzdt/202608/t20260814_680668.shtml'), '2026-08': ('2026年8月', 'https://www.mem.gov.cn/xw/yjglbgzdt/202609/t20260918_716876.shtml')}

class Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.editor_depth = 0
        self.p_depth = 0
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.editor_depth:
            if tag == 'div':
                self.editor_depth += 1
            if tag == 'p':
                self.p_depth += 1
        elif tag == 'div' and 'TRS_Editor' in attrs.get('class', '').split():
            self.editor_depth = 1

    def handle_data(self, text):
        if self.editor_depth and self.p_depth:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if self.editor_depth and tag == 'p' and self.p_depth:
            self.p_depth -= 1
            if not self.p_depth:
                text = re.sub('\\s+', ' ', ''.join(self.parts)).strip()
                self.parts = []
                if text:
                    self.paragraphs.append(text)
        if self.editor_depth and tag == 'div':
            self.editor_depth -= 1

def catalog():
    return {'source': '中华人民共和国应急管理部', 'coverage': '人工核实的六份通报，不是完整公报目录', 'reports': [{'id': key, 'period': title, 'url': url} for key, (title, url) in REPORTS.items()]}

def report(report_id, keyword=''):
    if report_id not in REPORTS:
        raise ValueError('未知报告 ID；请先查看目录')
    title, url = REPORTS[report_id]
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--compressed', '--max-time', '25', url], capture_output=True)
    if result.returncode:
        raise RuntimeError('上游请求失败：' + result.stderr.decode('utf-8', 'replace').strip())
    html = result.stdout.decode('utf-8', 'replace')
    parser = Paragraphs()
    parser.feed(html)
    if not parser.paragraphs:
        raise ValueError('未能识别正文，上游页面可能已变更')
    matched = [p for p in parser.paragraphs if keyword in p]
    return {'id': report_id, 'period': title, 'source_url': url, 'keyword': keyword, 'total_paragraphs': len(parser.paragraphs), 'matched_count': len(matched), 'paragraphs': matched, 'note': '返回官方原文段落；受灾人次不是去重人数。不同期次、统计口径及初步数据不可直接相加或简单比较；应核对原文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report_id', nargs='?', help='如 2025；省略时列目录')
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    try:
        print(json.dumps(report(a.report_id, a.keyword) if a.report_id else catalog(), ensure_ascii=False, indent=2))
    except Exception as e:
        p.exit(1, json.dumps({'error': str(e)}, ensure_ascii=False) + '\n')
