"""国家基本医保药品目录（2025年）PDF 逐页文字定位，本地快照。"""
import release_runtime
import argparse, json, sys
from pathlib import Path
DATA = Path(__file__).with_name('国家医保药品目录2025_逐页文字快照.json')

def load():
    d = json.loads(DATA.read_text(encoding='utf-8'))
    if len(d.get('pages', [])) != 202:
        raise ValueError('文字快照页数异常')
    return d

def insurance_page_search(keyword):
    if len(keyword.strip()) < 2:
        raise ValueError('关键词至少 2 字')
    d = load()
    pages = [x['page'] for x in d['pages'] if keyword in x['text']]
    return {'source': d['source'], 'source_url': d['source_url'], 'pdf_url': d['pdf_url'], 'pdf_sha256': d['pdf_sha256'], 'query': keyword, 'matched_pdf_pages': pages, 'note': '仅 PDF 提取文本中的字面匹配，PDF 页码为文件第几页，非正式印刷页码；表格结构、药品支付类别和条件必须核对官方原件，不代表当前个人可报销。'}

def insurance_page(page):
    d = load()
    if not 1 <= page <= len(d['pages']):
        raise ValueError('PDF 页码应为 1–202')
    return {'source_url': d['source_url'], 'pdf_url': d['pdf_url'], 'pdf_page': page, 'extracted_text': d['pages'][page - 1]['text'], 'note': '文字抽取可能打乱表格列或跨行；请务必核对 PDF 原始表格。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q = s.add_parser('page')
    q.add_argument('page', type=int)
    a = p.parse_args()
    print(json.dumps(insurance_page_search(a.keyword) if a.cmd == 'search' else insurance_page(a.page), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
