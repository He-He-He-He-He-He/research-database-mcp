"""国家统计局妇女及儿童发展纲要年度监测报告（指定报告）。"""
import release_runtime
import subprocess
from html.parser import HTMLParser
REPORTS = {'2024-children': {'title': '2024年《中国儿童发展纲要（2021—2030年）》统计监测报告', 'url': 'https://www.stats.gov.cn/sj/zxfbhjd/202512/t20251230_1962182.html'}, '2024-women': {'title': '2024年《中国妇女发展纲要（2021—2030年）》统计监测报告', 'url': 'https://www.stats.gov.cn/sj/zxfbhjd/202512/t20251230_1962183.html'}, '2023-children': {'title': '2023年《中国儿童发展纲要（2021—2030年）》统计监测报告', 'url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250124_1958440.html'}, '2023-women': {'title': '2023年《中国妇女发展纲要（2021—2030年）》统计监测报告', 'url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250124_1958439.html'}}

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.done = False
        self.skip = 0
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif not self.done and 'trs_editor_view' in dict(attrs).get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br')):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.done = True

def monitor_reports():
    return [{'id': k, **v} for k, v in REPORTS.items()]

def monitor_detail(report_id):
    if report_id not in REPORTS:
        raise ValueError('仅支持列出的报告')
    x = REPORTS[report_id]
    args = ['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', x['url']]
    html = release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8')
    p = _Body()
    p.feed(html)
    content = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(content) < 100:
        raise ValueError('未识别到报告正文')
    return {'id': report_id, **x, 'text': content, 'note': '年度统计监测报告正文；固定四份报告，非全站检索或完整数据库。'}
