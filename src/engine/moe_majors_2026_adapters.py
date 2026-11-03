"""教育部 2026 普通本科专业目录 PDF，本地页面文字检索。"""
import release_runtime
import argparse
import hashlib
import json
from pathlib import Path
PDF = Path(__file__).with_name('教育部普通本科专业目录2026.pdf')
SOURCE = 'https://www.moe.gov.cn/srcsite/A08/moe_1034/s3882/202604/W020260427440749576927.pdf'
NOTICE = 'https://www.moe.gov.cn/srcsite/A08/moe_1034/s3882/202604/t20260427_1434931.html'

def _reader():
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError('本接口需要 pypdf，使用 python3 -m pip install pypdf 安装') from exc
    if not PDF.is_file():
        raise FileNotFoundError('缺少附带的教育部本科专业目录 PDF')
    return PdfReader(PDF)

def info():
    reader = _reader()
    return {'title': '普通高等学校本科专业目录（2026年）', 'notice_url': NOTICE, 'source_pdf_url': SOURCE, 'sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(), 'pdf_pages': len(reader.pages), 'local_snapshot': PDF.name, 'note': '官网当次请求由 HTTPS 跳转至同域 HTTP；这是本地 2026 年 PDF 快照，目录并非高校招生计划，专业列表可能更新。'}

def page(number):
    r = _reader()
    if not isinstance(number, int) or isinstance(number, bool) or (not 1 <= number <= len(r.pages)):
        raise ValueError('页码必须在 PDF 页码范围内')
    return {'page': number, 'source_pdf_url': SOURCE, 'text': r.pages[number - 1].extract_text() or '', 'note': 'PDF 页码为文件中的页序，不一定等于印刷页码；文字抽取顺序可能与版面不同。'}

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 80:
        raise ValueError('关键词须为 1–80 字符')
    key = keyword.strip().casefold()
    r = _reader()
    out = []
    for n, p in enumerate(r.pages, 1):
        content = p.extract_text() or ''
        text = ' '.join(content.split())
        start = text.casefold().find(key)
        if start >= 0:
            out.append({'page': n, 'snippet': text[max(0, start - 100):min(len(text), start + len(key) + 160)]})
    return {'keyword': keyword.strip(), 'source_pdf_url': SOURCE, 'items': out, 'note': '关键词匹配抽取文字，每页只显示首处；PDF 排版和换行可能影响命中，专业代码、学位及修订须核对原版 PDF。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('info')
    s = sub.add_parser('search')
    s.add_argument('keyword')
    s = sub.add_parser('page')
    s.add_argument('number', type=int)
    args = p.parse_args()
    out = info() if args.command == 'info' else search(args.keyword) if args.command == 'search' else page(args.number)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
