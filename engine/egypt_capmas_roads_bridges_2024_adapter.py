"""Verified snapshot of CAPMAS 2024 roads and bridges bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/759/download/2247'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/759'
SHA256 = 'a5483327518f213ff8bb42ebb1ca9c798a25a85c0b6228d59f14b49bd2010649'
PAGES = 60

def _hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def _verify(path):
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified CAPMAS snapshot')
    with fitz.open(path) as document:
        if len(document) != PAGES:
            raise ValueError('Unexpected PDF page count')

def download(destination):
    path = release_runtime.expandpath(Path(destination))
    if os.path.lexists(path):
        raise FileExistsError('Destination already exists')
    if not path.parent.is_dir():
        raise ValueError('Destination directory does not exist')
    fd, tmp = tempfile.mkstemp(prefix='.capmas-roads-bridges-', suffix='.pdf', dir=path.parent)
    os.close(fd)
    try:
        try:
            release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '120', '--max-filesize', '20000000', '-o', tmp, URL], check=True, capture_output=True, timeout=125)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError('Official download failed: ' + type(exc).__name__) from None
        _verify(tmp)
        os.link(tmp, path)
        return {'path': str(path.absolute()), 'bytes': path.stat().st_size, 'sha256': SHA256, 'source_url': URL, 'pages': PAGES}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def page(path, page_number):
    if isinstance(page_number, bool) or not isinstance(page_number, int) or (not 1 <= page_number <= PAGES):
        raise ValueError('Physical page must be an integer between 1 and 60')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Bulletin of Enumerating Roads and Bridges Year 2023/2024', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。全国、主管部门与城市覆盖范围不同，不能作为 CBD 路网；原表单位及截止日期以原页为准。目录创建于 2025-06-04；当前 PDF 与截止时版本是否完全相同未证实。'}

def networks_by_authority(path):
    """Table 5: road network length by management entity."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    bounds = ((419, 455), (338, 377), (270, 305), (205, 231), (146, 179))
    with fitz.open(path) as doc:
        p = doc[22]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 11)).strip() for a, b in bounds] for y in (291.7, 317.7)]
        text = p.get_text()
    if rows != [['30373.4', '128996.5', '14651.7', '860.0', '174882'], ['17.4', '73.8', '8.4', '0.5', '100']] or 'Paved and Unpaved' not in text:
        raise RuntimeError('Road network table differs from reviewed original')
    names = ('General Authority for Roads and Bridges', 'Roads directorates / Localities', 'New Urban Communities Authority', 'National Company', 'Total')
    return {'source': 'CAPMAS Bulletin of Enumerating Roads and Bridges Year 2023/2024', 'source_url': URL, 'sha256': SHA256, 'physical_page': 23, 'printed_page': 16, 'table': 5, 'reference_date': '2024-06-30', 'unit': 'km', 'rows': [{'authority_as_printed': n, 'length_km': length, 'share_percent': share} for n, length, share in zip(names, *rows)], 'note': '表 5 标题涵盖铺装及土路，图表英文标题却仅称铺装道路，二者标题不一致，不能把表内数值单独作为铺装道路。主管方分项包含在全国总计内；NUCA 辖属网络并非 CBD 路网，也非道路通行状况。原表分项相加与总计存在 0.4 km 差异，原因未明；保留原始数。目录创建于 2025-06-04，但当前 PDF 与当时同版未证。'}
