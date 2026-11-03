"""Verified snapshot of CAPMAS 2024 vehicle and train accident bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/749/download/2205'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/749'
SHA256 = 'ffdf1fe8274a3fdf9556830ee8fd0a255b41b0cb82ddd1e39e718de4cd0c8af4'
PAGES = 62

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-road-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 62')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Annual Bulletin of Vehicles and Trains Accidents 2024', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。省级数据非 CBD，死亡人数非风险率。目录创建于 2025-05-15；当前 PDF 与截止时版本是否完全相同未证实。'}

def fatalities_selected(path):
    """Select sex and road-user breakdowns from original Tables 17 and 21."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as doc:
        p = doc[38]
        sex = [[p.get_textbox(fitz.Rect(a, y, b, y + 12)).strip() for a, b in ((404, 433), (294, 318), (183, 211))] for y in (170.5, 194.1, 467.2)]
        p = doc[42]
        users = [[p.get_textbox(fitz.Rect(a, y, b, y + 11)).strip() for a, b in ((414, 440), (357, 382), (302, 327), (245, 266), (181, 207))] for y in (155.7, 177.1, 453.2)]
        text = p.get_text()
    if sex != [['4397', '863', '5260'], ['634', '132', '766'], ['295', '70', '365']] or users != [['2125', '1202', '1174', '759', '5260'], ['456', '134', '94', '82', '766'], ['134', '70', '37', '124', '365']] or 'pass by the' not in text:
        raise RuntimeError('Road fatalities tables differ from reviewed original')
    areas = ('Total', 'Cairo', 'Giza')
    return {'source': 'CAPMAS Annual Bulletin of Vehicles and Trains Accidents 2024', 'source_url': URL, 'sha256': SHA256, 'year': '2024', 'sex_physical_page': 39, 'road_user_physical_page': 43, 'sex_rows': [{'area_as_printed': n, **dict(zip(('male', 'female', 'total'), r))} for n, r in zip(areas, sex)], 'road_user_rows': [{'area_as_printed': n, **dict(zip(('pass_by_the_road_as_printed', 'driver', 'passenger', 'other_unknown', 'total'), r))} for n, r in zip(areas, users)], 'note': '道路事故死亡人数，不是事故数、风险率或 CBD 数据。省级分项包含在全国，性别与道路用户为同一人群不同维度，不可叠加；pass by the road 沿用原刊表述，具体道路使用者定义见原刊。目录于 2025-05-15 创建，不能证实当前 PDF 与当时完全同版。'}
