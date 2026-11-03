"""查询2024、2025年市场监管总局公布的广告业数据（浙江省经济信息中心转载）。"""
import release_runtime
import argparse, html.parser, json, re, subprocess, sys
SOURCES = {2024: {'url': 'https://zjic.zj.gov.cn/ywdh/cyfz/202504/t20250411_23374933.shtml', 'original': 'https://www.samr.gov.cn/xw/zj/art/2025/art_0a0c3b8f56874d929cc6e61f836d36ce.html', 'credit': '新华社报道浙江省经济信息中心转载'}, 2025: {'url': 'https://zjic.zj.gov.cn/ywdh/jjyx/202604/t20260408_24025517.shtml', 'original': 'https://www.samr.gov.cn/xw/zj/art/2026/art_c26cc939029e4faf86674ff7ac0c1ee5.html', 'credit': '人民日报海外版报道浙江省经济信息中心转载'}}

class Text(html.parser.HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, t, a):
        if t in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, t):
        if t in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.parts.append(d)

def query(year):
    if year not in SOURCES:
        raise ValueError('仅支持 2024、2025 年')
    source = SOURCES[year]
    r = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '20', '--user-agent', 'ResearchCatalog/0.1 personal research', source['url']], capture_output=True, check=True)
    p = Text()
    p.feed(r.stdout.decode('utf-8'))
    text = re.sub('\\s+', '', ''.join(p.parts))
    raw_values = {}

    def number(pattern, name, required=True):
        m = re.search(pattern, text)
        if not m and required:
            raise ValueError('网页未含预期字段，无法可靠解析')
        raw_values[name] = m.group(1) if m else None
        return float(m.group(1)) if m else None
    total = number(str(year) + '年.{0,50}?广告业务收入.{0,40}?达([\\d.]+)亿元', '广告业务收入')
    publication = number(str(year) + '年.{0,1800}?互联网广告发布收入(?:为|达)?([\\d.]+)亿元', '互联网广告发布收入')
    business = number('互联网广告业务收入(?:为|达)?([\\d.]+)亿元', '互联网广告业务收入', False) if year == 2025 else None
    raw_values.setdefault('互联网广告业务收入', None)
    return {'indicators_raw': raw_values, 'data_year': year, 'source_name': '国家市场监督管理总局公布数据', 'access_url': source['url'], 'original_source_url': source['original'], 'access_provenance': source['credit'], 'unit': '亿元', 'scope': '全国事业单位和规模以上企业', 'indicators': {'广告业务收入': total, '互联网广告发布收入': publication, '互联网广告业务收入': business}, 'note': '业务收入与发布收入统计环节不同，不能混用；null表示此页面未提供。原总局网站本机返回403，数据读取自标明来源的浙江省政府网站转载。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=(2024, 2025))
    a = p.parse_args()
    print(json.dumps(query(a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
