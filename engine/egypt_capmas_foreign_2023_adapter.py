"""Verified snapshot of CAPMAS 2024 foreign workers bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/733/download/2120'
CATALOG_URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/733'
SHA256 = 'd6a5401659ba76c3c0df4cbe83a18f8a1a0627342ccc270341f745d6d360dc83'
PAGES = 33

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-foreign-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 33')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Annual Bulletin of Foreign Employees in Private and Investment Sectors 2023', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。所列仅私营与投资部门获得工作许可的外国人，非全部外籍人口或 CBD 工作人员；许可发放地区不一定为工作地点。目录创建于 2024-10-27；当前 PDF 与截止时版本是否完全相同未证实。'}

def asian_nationalities(path):
    """Selected rows in Table 3's non-Arab Asian countries section."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    bounds = [(537, 561), (486, 505), (429, 454), (376, 401), (325, 344), (268, 294), (212, 242), (160, 187)]
    with fitz.open(path) as doc:
        p = doc[15]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 14)).strip() for a, b in bounds] for y in (230.3, 269.0, 288.3)]
        text = p.get_text()
    expected = [['1974', '389', '2363', '3626', '286', '3912', '6275', '-'], ['436', '16', '452', '1192', '14', '1206', '1658', '26.4'], ['650', '54', '704', '531', '30', '561', '1265', '20.2']]
    if rows != expected or 'Asian countries (Non-Arab)' not in text:
        raise RuntimeError('Nationality table differs from reviewed original')
    keys = ['first_male', 'first_female', 'first_total', 'renewal_male', 'renewal_female', 'renewal_total', 'total', 'percent_of_group_as_printed']
    return {'source': 'CAPMAS Annual Bulletin of Foreign Employees in Private and Investment Sectors in Egypt 2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 16, 'printed_page': 11, 'table': '3 (continued)', 'year_as_printed': '2023', 'rows': [{'nationality_or_group_as_printed': n, **dict(zip(keys, row))} for n, row in zip(('Total: Asian countries (Non-Arab)', 'India', 'China'), rows)], 'note': '仅私营与投资部门获得工作许可的外籍人员，非全部外籍人士、CBD 人员或实际唯一工作人口；首次和续期为原表合同类别。百分比以非阿拉伯亚洲组 6275 为分母，不能当全国份额；国籍、性别、续期分项和总计重叠，不可重复加总。原站目录同时含 2017、2023、2024 时间字段，与标题不一致；当前 PDF 与 2024 年建目录时是否同版未证。'}
