"""Verified snapshot of CAPMAS 2024 housing bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/673/download/1996'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/673'
SHA256 = 'd28bd1bfa57b5b1e2b5bddb2ecc2d8ae5ab3fb2c14db44844fc2ae113b361004'
PAGES = 47

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-housing-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 47')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Housing Bulletin in Egypt 2022/2023', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。原刊目录标题倒序写 2023/2022，封面和表格为 2022/2023；城市、地区与 CBD 范围不可混同。目录创建于 2024-03-17；当前 PDF 与截止时版本是否完全相同未证实。'}

def luxury_projects(path):
    """Read visually verified cells in Table 25; preserve source strings."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        p = document[40]
        bounds = [(390, 420), (315, 350), (248, 283)]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 12)).strip() for a, b in bounds] for y in (222.5, 254.5, 301.5)]
        text = p.get_text()
    if rows != [['1432', '45512', '15657'], ['560', '9694', '2689'], ['0', '21930', '3964']] or 'Third' not in text or 'Fifth district' not in text:
        raise RuntimeError('Table 25 differs from the reviewed original')
    keys = ('implemented_units', 'under_implementation_units', 'investments_million_egyptian_pounds')
    names = ('All listed NUCA luxury housing projects', 'Administrative capital (Third district)', 'Administrative capital (Fifth district)')
    return {'source': 'CAPMAS Housing Bulletin in Egypt 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 41, 'printed_page': 34, 'table': 25, 'period': '2022/2023', 'rows': [{'area_as_printed': name, **dict(zip(keys, row))} for name, row in zip(names, rows)], 'note': 'NUCA 监管豪华住房原表；全部项目的总计包括其他城市，与首都分项重叠。新行政首都第三、第五行政区不是 CBD 项目，已建和在建不是入住或出租数；投资为原表百万埃镑，投入时间与付款口径未确认。目录 2024-03-17 建立，当前 PDF 与当时版本是否完全一致未知；文字抽取应与原页复核。'}

def luxury_history(path):
    """Table 24 yearly implemented homes and comparison to Table 25."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    bounds = [(412, 442), (360, 387), (305, 335), (252, 282), (198, 228), (153, 190)]
    with fitz.open(path) as document:
        p = document[39]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 13)).strip() for a, b in bounds] for y in (197.5, 226.3)]
        text = p.get_text()
    if rows != [['5220', '178', '3921', '4764', '1432', '15515'], ['4900', '178', '3898', '4764', '560', '14300']] or 'Administrative' not in text:
        raise RuntimeError('Table 24 differs from the reviewed original')
    keys = ('2018/2019', '2019/2020', '2020/2021', '2021/2022', '2022/2023', 'total_as_printed')
    return {'source': 'CAPMAS Housing Bulletin in Egypt 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 40, 'printed_page': 33, 'table': 24, 'unit': 'implemented housing units', 'rows': [{'area_as_printed': 'All listed NUCA luxury housing projects', **dict(zip(keys, rows[0]))}, {'area_as_printed': 'Administrative capital', **dict(zip(keys, rows[1]))}], 'note': '2018/19—2022/23 为该期间分年度已实施住房数，原表合计是这五年之和，不代表首都全部住房存量、CBD 或入住率。表 24 首都 2022/23 的 560 与同刊表 25 首都第三区 560 同值，不可相加；跨表范围是否完全一致仍须核实。总计包括其他城市并与首都重叠。官方目录创建于 2024-03-17；当前 PDF 与当时文件完全一致未确认。'}
