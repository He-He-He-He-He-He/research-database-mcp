"""《科普研究》2024年第十四次公民科学素质抽样调查报告正文检索。"""
import release_runtime
import argparse
import json
from pathlib import Path
SOURCE = 'https://castjournals.cast.org.cn/joweb/kpyj/CN/1240340550864400698'
SNAPSHOT = Path(__file__).parent / '数据/中国公民科学素质调查/2024.html'

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError('需要 Beautiful Soup 4') from exc
    soup = BeautifulSoup(SNAPSHOT.read_text(encoding='utf-8'), 'html.parser')
    paragraphs = []
    for item in soup.select('.mag_main_zhengwen_left_div_p'):
        text = item.get_text(' ', strip=True)
        if ''.join(keyword.split()) in ''.join(text.split()):
            paragraphs.append({'paragraph_id': item.get('id'), 'text': text})
    if not soup.select_one('.mag_main_zhengwen_left_div_p'):
        raise ValueError('原网页正文结构不可识别')
    return {'source': SOURCE, 'survey_year': 2024, 'keyword': keyword, 'items': paragraphs, 'note': '期刊公开文章正文快照；图表图像未解析。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
