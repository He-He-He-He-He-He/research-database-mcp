"""2018年全国未成年人互联网使用情况研究报告转载本正文查询。"""
import release_runtime
import argparse
import json
from pathlib import Path
FILE = Path(__file__).parent / '数据/未成年人互联网调查/2018.pdf'
SOURCE = 'https://cnlgbtdata.com/files/uploads/2019/04/P020190326787104688503.pdf'
ANNOUNCEMENT = 'https://www.cac.gov.cn/2020-04/16/c_1588583175971355.htm'

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
    return {'survey_year': 2018, 'source_copy': SOURCE, 'announcement': ANNOUNCEMENT, 'keyword': keyword, 'pages': pages, 'note': '第三方转载 PDF；图片未识别。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
