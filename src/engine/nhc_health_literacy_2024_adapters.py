"""2024年全国居民健康素养监测：原报告检索与城乡地区表。"""
import release_runtime
import argparse
import json
from pathlib import Path
PDF = Path(__file__).parent / '数据/居民健康素养监测/2024.pdf'
SOURCE = 'https://www.gov.cn/lianbo/bumen/202501/P020250110406390443744.pdf'

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('报告检索需要安装 PyMuPDF') from exc
    with fitz.open(PDF) as doc:
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if ''.join(keyword.split()) in ''.join(text.split()):
                pages.append({'page': i + 1, 'text': text})
    return {'year': 2024, 'source': SOURCE, 'keyword': keyword, 'pages': pages}

def table():
    values = [('城乡', '城市', 34.74), ('城乡', '农村', 29.11), ('地区', '东部', 34.98), ('地区', '中部', 31.48), ('地区', '西部', 27.27), ('全国', '全国', 31.87)]
    return {'year': 2024, 'source': SOURCE, 'page': 4, 'unit': '%', 'indicator': '健康素养水平', 'rows': [{'group': g, 'category': c, 'value': v} for g, c, v in values], 'note': '15—69岁常住人口；报告结果为经调查权重调整的数据，非原始样本比例。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('table')
    q = s.add_parser('search')
    q.add_argument('keyword')
    args = p.parse_args()
    print(json.dumps(table() if args.cmd == 'table' else search(args.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
