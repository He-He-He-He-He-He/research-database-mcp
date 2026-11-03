"""Zhejiang ecology authority's official 2024 environmental status bulletin PDF."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URL = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web1756/site/attach/0/38a755a3dc3a4a4ab4e84c84590c9c97.pdf'

def pages(keyword=''):
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF'):
        raise ValueError('official response is not PDF')
    doc = PdfReader(io.BytesIO(r.content))
    found = []
    for n, page in enumerate(doc.pages, 1):
        text = page.extract_text() or ''
        if keyword in text:
            found.append({'pdf_page': n, 'text': text})
    if not keyword and (not any((p['text'].strip() for p in found))):
        raise ValueError('no extractable text')
    return {'source': '浙江省生态环境厅', 'year': 2024, 'source_url': URL, 'page_count': len(doc.pages), 'pages': found}
