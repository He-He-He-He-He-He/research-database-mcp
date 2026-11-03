"""Search text blocks in two conflicting official Saudi population infographics."""
import release_runtime
import subprocess, fitz
URLS = {'v2067012': 'https://www.stats.gov.sa/documents/20117/2067012/Population%2BEstimates%2BStatistics%2B2024%2BEN.pdf/9b71e303-5fd9-19cb-9913-850a9d521639', 'v2435273': 'https://www.stats.gov.sa/documents/20117/2435273/Population%2BEstimates%2BPublication%2B2024%2BEN.pdf/7d123c57-1626-7d2f-ba7f-8a719f928f28'}

def search(keyword, version='v2435273', limit=4):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (version not in URLS):
        raise ValueError('Invalid keyword or version')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit must be 1–10')
    u = URLS[version]
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '30', '--max-filesize', '3000000', u], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Saudi statistics download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 3000000 or not p.stdout.startswith(b'%PDF'):
        raise RuntimeError('Invalid Saudi statistics PDF')
    with fitz.open(stream=p.stdout, filetype='pdf') as doc:
        if len(doc) != 1:
            raise RuntimeError('Unexpected infographic pagination')
        blocks = doc[0].get_text('blocks')
    result = []
    for block in blocks:
        text = block[4].strip()
        if keyword.casefold() in text.casefold():
            result.append({'pdf_page': 1, 'bbox': [round(v, 1) for v in block[:4]], 'text': text})
    return {'source': 'Saudi General Authority for Statistics', 'title': 'Population Estimates Publication 2024', 'selected_version': version, 'pdf_url': u, 'alternate_version_url': URLS['v2067012' if version == 'v2435273' else 'v2435273'], 'query': keyword, 'matches': len(result), 'items': result[:limit], 'note': 'One-page infographic: extracted blocks retain text but may omit chart context or have reading-order errors. Two official English versions disagree on the reported fertility rate for the total population (2.0 vs 2.1) and use unclear birth-rate units; verify official definitions and revision history before citing. Population values are estimates, not census counts.'}
