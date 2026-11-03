"""交通运输部年度公报全国货运及跨区域人员流动指标，逐年读取。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from research import fetch
SOURCES = {2024: 'https://xxgk.mot.gov.cn/2020/jigou/zhghs/202506/t20250610_4170228.html', 2025: 'https://xxgk.mot.gov.cn/jigou/zhghs/202606/t20260618_4207752.html'}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div' and (not self.depth) and ('TRS_UEDITOR' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.found = True
            return
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t in ('p', 'br'):
                self.parts.append('\n')

    def handle_data(self, d):
        if self.depth:
            self.parts.append(d)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1
        elif t == 'p' and self.depth:
            self.parts.append('\n')

def year_data(year):
    if year not in SOURCES:
        raise ValueError('目前仅支持 2024 和 2025 年')
    p = Body()
    p.feed(fetch(SOURCES[year]))
    if not p.found:
        raise ValueError('未找到公报正文')
    paragraphs = ''.join(p.parts).split('\n')
    candidates = [s.strip() for s in paragraphs if '全年完成营业性货运量' in s and '跨区域人员流动量' in s]
    if len(candidates) != 1:
        raise ValueError('全国运输总述段落无法唯一识别，请核对原文')
    line = candidates[0]
    pats = {'freight_100m_tonnes': '全年完成营业性货运量([\\d.]+)亿吨', 'freight_turnover_100m_tonne_km': '完成货物周转量([\\d.]+)亿吨公里', 'cross_region_person_trips_100m': '跨区域人员流动量([\\d.]+)亿人次'}
    values = {}
    for name, pat in pats.items():
        m = re.search(pat, line)
        if not m:
            raise ValueError('无法读取指标 ' + name + '，请核对公报')
        values[name] = m.group(1)
    return {'year': year, 'source': SOURCES[year], 'values': values, 'source_paragraph': line, 'note': '数据按公报口径；原文及注释是判断年度可比性的依据'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('years', nargs='*', type=int, default=[2024, 2025])
    a = p.parse_args()
    print(json.dumps({'series': [year_data(y) for y in a.years]}, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
