"""2025 年全国软件业运行原文；福建省工信厅转载工信部数据。"""
import release_runtime
import argparse, json, requests
from bs4 import BeautifulSoup
URL = 'https://gxt.fj.gov.cn/zwgk/gysj/xysj/xxcy/202604/t20260429_7132836.htm'
ORIGINAL = 'https://www.miit.gov.cn/gxsj/tjfx/rjy/art/2026/art_65a12a560865432bb1548fdddc74f19c.html'

def software_report(keyword=None, timeout=15):
    if keyword is not None and (not isinstance(keyword, str) or len(keyword) > 100):
        raise ValueError('关键词无效')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    b = s.select_one('.TRS_Editor')
    if b is None:
        raise ValueError('正文缺失')
    paragraphs = [p.get_text('', strip=True) for p in b.find_all('p') if p.get_text('', strip=True)]
    if not any(('软件业务收入154831亿元' in p for p in paragraphs)):
        raise ValueError('报告标题或数据已变化')
    rows = [p for p in paragraphs if keyword is None or keyword in p]
    return {'source': '工信部运行监测协调局（福建省工信厅转载）', 'source_url': URL, 'original_url': ORIGINAL, 'year': 2025, 'keyword_filter': keyword, 'paragraphs': rows, 'note': '仅返回正文段落，不读取图片图表；软件业务收入与出口分别以亿元人民币和亿美元计，指标含包含关系。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword')
    a = p.parse_args()
    print(json.dumps(software_report(a.keyword), ensure_ascii=False, indent=2))
