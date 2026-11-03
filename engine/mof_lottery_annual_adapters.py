"""财政部公布的全国彩票年度销售额，来自12月累计统计。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from research import fetch
SOURCES = {2023: 'https://www.mof.gov.cn/jrttts/202401/t20240130_3927767.htm', 2024: 'https://zhs.mof.gov.cn/zonghexinxi/202501/t20250124_3955089.htm', 2025: 'https://zhs.mof.gov.cn/zonghexinxi/202601/t20260128_3982699.htm'}

class Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_p = False
        self.current = []
        self.paragraphs = []

    def handle_starttag(self, t, a):
        if t == 'p':
            self.in_p = True
            self.current = []

    def handle_data(self, d):
        if self.in_p:
            self.current.append(d)

    def handle_endtag(self, t):
        if t == 'p' and self.in_p:
            self.paragraphs.append(''.join(self.current).strip())
            self.in_p = False

def year_data(year):
    if year not in SOURCES:
        raise ValueError('目前仅支持 2023、2024、2025 年')
    p = Paragraphs()
    p.feed(fetch(SOURCES[year]))
    lines = [s for s in p.paragraphs if '1-12月累计' in s and '全国共销售彩票' in s and ('福利彩票机构销售' in s) and ('体育彩票机构销售' in s)]
    if len(lines) != 1:
        raise ValueError('年度累计段落未能唯一识别')
    line = lines[0]
    patterns = {'total_100m_yuan': '全国共销售彩票([\\d.]+)亿元', 'welfare_100m_yuan': '福利彩票机构销售([\\d.]+)亿元', 'sports_100m_yuan': '体育彩票机构销售([\\d.]+)亿元'}
    values = {}
    for key, pat in patterns.items():
        match = re.search(pat, line)
        if not match:
            raise ValueError('未识别指标 ' + key)
        values[key] = match.group(1)
    return {'year': year, 'source': SOURCES[year], 'values': values, 'source_paragraph': line, 'unit': '亿元', 'scope': '1—12月累计，统计口径详见官方公告'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('years', nargs='*', type=int, default=[2023, 2024, 2025])
    a = p.parse_args()
    print(json.dumps({'series': [year_data(y) for y in a.years]}, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
