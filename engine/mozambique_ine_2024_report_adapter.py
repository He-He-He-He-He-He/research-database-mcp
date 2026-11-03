"""INE Mozambique 2024 agriculture and environment report PDF text blocks."""
import release_runtime
import subprocess, fitz
REPORTS = {'agriculture': {'url': 'https://www.ine.gov.mz/documents/20119/169249/Indicadores%20B%C3%A1sicos%20de%20Agricultura%20e%20Alimenta%C3%A7%C3%A3o%202024.pdf/67b74690-60bf-267f-28a7-130f689fcecc?download=true', 'title': 'Indicadores Básicos de Agricultura e Alimentação 2024'}, 'environment': {'url': 'https://ine.gov.mz/documents/20119/105462/Estat%C3%ADsticas%20do%20Ambiente%2C%202024.pdf/0fbdc4e1-871d-954c-5d21-294de83d821e?download=true', 'title': 'Estatísticas do Ambiente 2024'}}

def search(report, keyword, offset=0, limit=5):
    if report not in REPORTS or not isinstance(keyword, str) or (not keyword.strip()) or (len(keyword) > 100):
        raise ValueError('invalid report or keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 20):
        raise ValueError('invalid offset or limit')
    info = REPORTS[report]
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '75', '--max-filesize', '25000000', info['url']], capture_output=True, timeout=80)
    if p.returncode:
        raise RuntimeError('INE Mozambique download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 25000000 or not p.stdout.startswith(b'%PDF'):
        raise RuntimeError('Invalid PDF')
    blocks = []
    with fitz.open(stream=p.stdout, filetype='pdf') as doc:
        if len(doc) > 150:
            raise RuntimeError('Report unexpectedly large')
        page_count = len(doc)
        for n, page in enumerate(doc):
            for block in page.get_text('blocks'):
                t = block[4].strip()
                if keyword.casefold() in t.casefold():
                    blocks.append({'pdf_page': n + 1, 'bbox': [round(v, 1) for v in block[:4]], 'text': t})
    return {'source': 'Instituto Nacional de Estatística, Moçambique', 'title': info['title'], 'url': info['url'], 'pdf_pages': page_count, 'keyword': keyword, 'matching_blocks': len(blocks), 'offset': offset, 'items': blocks[offset:offset + limit], 'note': 'Official reports contain differing 2024 population estimates: agriculture report 33,244,414; environmental report 34,213,239. Do not silently reconcile; check definitions, release versions, and methodology. Blocks may omit neighbouring table headers, charts, footnotes or have reading-order defects; verify original PDF. Annual estimates/projections are not a census count.'}
