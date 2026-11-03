"""Verified snapshot of CAPMAS 2024 fire accident report."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/750/download/2208'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/750'
SHA256 = '931ff38eaa03a2648a2f9fdde7d9d569f15cce0ec467bd07abb879e3f724fc88'
PAGES = 29

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-fire-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 29')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Annual Report of Fire Accidents in Egypt 2024', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。省级数据非 CBD，火灾次数及死亡人数非风险率；原文 industrial fires 包含烟头、火柴等，不可称工业设施火灾。目录创建于 2025-05-15；当前 PDF 与截止时版本是否完全相同未证实。'}

def governorates_and_causes(path):
    """Selected directly checked rows from fire bulletin tables 3 and 11."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as doc:
        p = doc[15]
        geo = [[p.get_textbox(fitz.Rect(a, y, b, y + 12)).strip() for a, b in ((368, 400), (248, 272))] for y in (119, 139.4, 160.0)]
        p = doc[23]
        causes = [p.get_textbox(fitz.Rect(a, 173, b, 185)).strip() for a, b in ((486, 516), (392, 418), (213, 244), (172, 202))]
        summary = doc[10].get_text()
    if geo != [['46925', '100'], ['6288', '13.4'], ['3790', '8.1']] or causes != ['14817', '8428', '21692', '46925'] or 'cigarette butts' not in summary:
        raise RuntimeError('Fire bulletin tables differ from reviewed original')
    return {'source': 'CAPMAS Annual Report of Fire Accidents in Egypt 2024', 'source_url': URL, 'sha256': SHA256, 'year': '2024', 'geography_physical_page': 16, 'causes_physical_page': 24, 'categories_explanation_physical_page': 11, 'geography': [{'area_as_printed': n, 'fire_accidents': r[0], 'share_percent': r[1]} for n, r in zip(('Total', 'Cairo', 'Giza'), geo)], 'selected_national_causes': dict(zip(('industrial_fires_as_printed', 'electrical_short_circuit_or_friction', 'undefined', 'total'), causes)), 'note': '省份与全国、原因与总计重叠，无法跨维度相加；火灾次数并非风险率或 CBD 数据。industrial fires 原刊举例包括烟头、火柴与可燃材料，不等于工业场所火灾。未明原因占比高；目录于 2025-05-15 创建，但当前 PDF 是否与当时同版未证。'}
