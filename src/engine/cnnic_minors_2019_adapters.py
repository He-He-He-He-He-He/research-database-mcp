"""2019年全国未成年人互联网使用情况研究报告正文查询。"""
import release_runtime
import argparse
import json
from pathlib import Path
FILE = Path(__file__).parent / '数据/未成年人互联网调查/2019.pdf'
SOURCE = 'https://news.youth.cn/gn/202005/W020200513320996080332.pdf'
ANNOUNCEMENT = 'https://www.cac.gov.cn/2020-05/13/c_1590919071365700.htm'

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('需要 PyMuPDF') from exc
    pages = []
    with fitz.open(FILE) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if ''.join(keyword.split()) in ''.join(text.split()):
                pages.append({'pdf_page': i + 1, 'text': text})
    return {'survey_year': 2019, 'source_copy': SOURCE, 'announcement': ANNOUNCEMENT, 'keyword': keyword, 'pages': pages, 'note': 'PDF文本检索；图像与图表未识别。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
