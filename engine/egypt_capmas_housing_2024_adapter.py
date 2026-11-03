"""Verified snapshot of CAPMAS 2024 housing bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/810/download/2394'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/810'
SHA256 = 'c94a106ae7e7d83b89def97ec4669dd32a9174cba48139f18cec49ed7decf63a'
PAGES = 48

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-housing24-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 48')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Housing Bulletin in Egypt 2023/2024', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。城市、地区与 CBD 范围不可混同。阿文目录 2025-06-01 创建，但英文目录 2025-12-14 创建，当前英文 PDF 在 2025-06-30 前是否已公开及是否同版均未证实。'}
