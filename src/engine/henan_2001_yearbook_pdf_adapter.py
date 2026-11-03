"""Henan Provincial Bureau of Statistics 2001 yearbook, official scanned PDF."""
import release_runtime
import requests
URL = 'https://xcoss.henan.gov.cn/typtfile/20250321/64f43d6b7a494fa885ecbc35dff768db.pdf'

def document():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {'source': '河南省统计局《河南统计年鉴2001》', 'edition': 2001, 'url': URL, 'content_type': 'application/pdf', 'content': r.content}
