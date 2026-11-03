"""生态环境部《国家危险废物名录（2025年版）》官方 PDF 页检索。"""
import release_runtime
import hashlib
import requests, fitz
SOURCE = 'https://www.mee.gov.cn/xxgk2018/xxgk/xxgk02/202411/t20241129_1097685.html'
PDF = 'https://www.mee.gov.cn/xxgk2018/xxgk/xxgk02/202411/W020241129617875148704.pdf'

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字符')
    r = requests.get(PDF, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 10000000 or (not r.content.startswith(b'%PDF-')):
        raise ValueError('未获取有效 PDF')
    doc = fitz.open(stream=r.content, filetype='pdf')
    if len(doc) > 150:
        raise ValueError('PDF 超出页数限制')
    hits = []
    for page in doc:
        text = page.get_text()
        if keyword.strip().casefold() in text.casefold():
            hits.append({'page': page.number + 1, 'text': text})
    return {'source': '生态环境部等五部门《国家危险废物名录（2025年版）》', 'source_url': SOURCE, 'pdf_url': PDF, 'sha256': hashlib.sha256(r.content).hexdigest(), 'keyword': keyword.strip(), 'hits': hits, 'note': '原 PDF 物理页码与印刷页码可能不同；仅检索可提取文字，图表或扫描页不保证识别。危废识别须结合名录条文、附表、豁免清单和专业鉴别；无匹配不代表非危险废物，也不证明现行效力未变化。'}
