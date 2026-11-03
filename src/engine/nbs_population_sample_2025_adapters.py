"""从国家统计局 2025 年 1% 人口抽样调查公报提取部分明确指标。"""
import release_runtime
import json
import re
import subprocess
from html.parser import HTMLParser
URL = 'https://www.stats.gov.cn/zt_18555/zdtjgz/cydc/2025cydc/tzgg/202605/t20260522_1963788.html'

class _Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.current = None
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.current = []

    def handle_data(self, text):
        if self.current is not None:
            self.current.append(text)

    def handle_endtag(self, tag):
        if tag == 'p' and self.current is not None:
            text = ''.join(self.current).strip()
            if text:
                self.paragraphs.append(text)
            self.current = None

def population_2025():
    raw = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', URL], capture_output=True, check=True).stdout.decode('utf-8')
    p = _Paragraphs()
    p.feed(raw)
    spec = [('全国人口', '全国人口为', '全国人口为([\\d.]+)万人', '万人'), ('男性人口', '全国人口为', '男性人口为([\\d.]+)万人', '万人'), ('女性人口', '全国人口为', '女性人口为([\\d.]+)万人', '万人'), ('0—14岁人口', '0—14岁人口为', '0—14岁人口为([\\d.]+)万人', '万人'), ('15—59岁人口', '0—14岁人口为', '15—59岁人口为([\\d.]+)万人', '万人'), ('60岁及以上人口', '0—14岁人口为', '60岁及以上人口为([\\d.]+)万人', '万人'), ('65岁及以上人口', '0—14岁人口为', '65岁及以上人口为([\\d.]+)万人', '万人'), ('城镇人口', '居住在城镇的人口为', '居住在城镇的人口为([\\d.]+)万人', '万人'), ('乡村人口', '居住在城镇的人口为', '居住在乡村的人口为([\\d.]+)万人', '万人')]
    items = []
    for label, anchor, pattern, unit in spec:
        paragraphs = list(dict.fromkeys((x for x in p.paragraphs if anchor in x)))
        if len(paragraphs) != 1:
            raise ValueError('未能唯一定位公报段落：' + label)
        match = re.search(pattern, paragraphs[0])
        if not match:
            raise ValueError('公报指标格式变化：' + label)
        items.append({'indicator': label, 'value': match.group(1), 'unit': unit, 'source_text': paragraphs[0]})
    return {'source_url': URL, 'reference_time': '2025-11-01 00:00', 'published_date': '2026-05-22', 'method': '全国1%人口抽样调查，公报估计全国人口；包括根据质量抽查计算的漏登人口', 'items': items, 'note': '年龄组是层级关系，65岁及以上包含在60岁及以上内，不应相加；户籍、城乡及常住人口口径、港澳台和外籍人员范围请核对原文。抽样与普查不是同一调查。'}
if __name__ == '__main__':
    print(json.dumps(population_2025(), ensure_ascii=False, indent=2))
