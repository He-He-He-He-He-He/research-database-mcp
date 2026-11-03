"""生态环境部2025年居民生态环境健康素养监测原文与结果。"""
import release_runtime
import argparse
import json
from pathlib import Path
SOURCE = 'https://www.mee.gov.cn/ywgz/fgbz/hjyjk/gzdt/202604/U020260427637516068253.pdf'
PDF = Path(__file__).parent / '数据/生态环境健康素养/2025.pdf'

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('原文检索需要 PyMuPDF') from exc
    with fitz.open(PDF) as doc:
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if ''.join(keyword.split()) in ''.join(text.split()):
                pages.append({'page': i + 1, 'text': text})
    return {'survey_year': 2025, 'source': SOURCE, 'keyword': keyword, 'pages': pages}

def indicators():
    rows = [('总体', '全国', 22.6, 6), ('分类', '基本理念', 38.7, 7), ('分类', '基本知识', 19.3, 7), ('分类', '基本行为和技能', 22.8, 7), ('城乡', '城市', 28.7, 8), ('城乡', '农村', 18.0, 8), ('年龄', '15—17岁', 30.9, 9), ('年龄', '18—34岁', 36.2, 9), ('年龄', '35—49岁', 21.1, 9), ('年龄', '50—69岁', 11.2, 9)]
    return {'survey_year': 2025, 'source': SOURCE, 'unit': '%', 'rows': [{'group': g, 'name': n, 'value': v, 'pdf_page': p} for g, n, v, p in rows], 'note': '数据摘录报告正文，分组分母以报告和原始方法为准；调查样本及评价定义见原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('indicators')
    q = s.add_parser('search')
    q.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(indicators() if a.command == 'indicators' else search(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
