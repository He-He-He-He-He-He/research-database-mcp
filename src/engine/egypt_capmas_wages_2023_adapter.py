"""Verified snapshot of CAPMAS 2024 employment and wages bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/ar/index.php/catalog/1920/download/6924'
CATALOG_URL = 'https://metadata.capmas.gov.eg/ar/index.php/catalog/1920'
SHA256 = 'a045d5f2d6da614b7bc0d754f4c8bc9698d20732e5afab43354d9e1ebf452676'
PAGES = 161

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-wages-', suffix='.pdf', dir=path.parent)
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
        raise ValueError('Physical page must be an integer between 1 and 161')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Annual bulletin of employment wages and working hours 2023', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。工资为调查口径平均月工资而非最低工资或 CBD 薪酬，包含公共和私营部门，详见原刊抽样方法。目录创建于 2025-06-02；当前 PDF 与截止时版本是否完全相同未证实。'}

def governorate_wages(path):
    """Read selected visually reviewed rows from the June 2023 original table."""
    _verify(release_runtime.expandpath(Path(path)))
    bounds = [(444, 476), (423, 442), (398, 414), (363, 392), (340, 359), (316, 332), (280, 311), (253, 273), (220, 237)]
    with fitz.open(release_runtime.expandpath(Path(path))) as doc:
        p = doc[35]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 10)).strip() for a, b in bounds] for y in (194.5, 213.2, 456.6)]
        text = p.get_text()
    expected = [['11754869', '5128', '209', '2547370', '4439', '186', '14302240', '5005', '205'], ['2252244', '7886', '202', '581659', '6102', '185', '2833902', '7520', '198'], ['1692903', '5749', '189', '492738', '4886', '164', '2185641', '5554', '183']]
    if rows != expected or 'June' not in text or '2023' not in text:
        raise RuntimeError('Wage table differs from reviewed original')
    keys = ('male_employees', 'male_cash_wage_egp_month', 'male_hours_month', 'female_employees', 'female_cash_wage_egp_month', 'female_hours_month', 'total_employees', 'total_cash_wage_egp_month', 'total_hours_month')
    return {'source': 'CAPMAS Annual bulletin of employment wages and working hours 2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 36, 'printed_page': 31, 'reference_period': 'June 2023', 'rows': [{'area_as_printed': n, **dict(zip(keys, r))} for n, r in zip(('Total', 'Cairo', 'Giza'), rows)], 'note': '表格标题为 2023 年 6 月，机构调查结果：公共/公共企业及私营部门，工资为月均现金工资（埃镑），工时为月平均；抽样和加权见原刊方法。就业人数为调查估计，非所有居民；全国男女人数之和比总数少 1，Cairo 男女之和比总数多 1，原因未说明，保留原值；全国与省份、总计与性别列重叠，不可相加。名义历史月工资非 CBD 薪资、法定最低工资或现时工资；目录建立日期不证明当前 PDF 与当时完全同版。'}

def industry_wages(path):
    """Table of selected activity estimates, preserving printed values."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    bounds = [(268, 291), (240, 258), (214, 230)]
    with fitz.open(path) as doc:
        p = doc[32]
        rows = [[p.get_textbox(fitz.Rect(a, y, b, y + 8)).strip() for a, b in bounds] for y in (343.5, 368.5, 421.2, 446.2, 521.0, 571.0)]
        table = p.get_text()
        summary = doc[31].get_text()
    expected = [['94933', '6939', '187'], ['143231', '7340', '190'], ['604963', '4816', '220'], ['843424', '3771', '221'], ['27514', '3409', '179'], ['157843', '3917', '198']]
    if rows != expected or 'Construction and building 221 hours' not in summary or 'June 2023' not in table:
        raise RuntimeError('Industry wage table differs from reviewed original')
    names = ['Water supply, sewage networks, waste management and treatment', 'Construction and building', 'Transportation and storage', 'Food and accommodation services', 'Real Estate Leasing', 'Administrative activities and support services']
    keys = ['estimated_employees', 'average_monthly_cash_wage_egp', 'average_monthly_working_hours']
    return {'source': 'CAPMAS Annual bulletin of employment wages and working hours 2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 33, 'printed_page': 28, 'summary_physical_page': 32, 'reference_period': 'June 2023', 'rows': [{'activity_as_printed': name, **dict(zip(keys, row))} for name, row in zip(names, rows)], 'note': '公共/公共企业及私营机构调查按行业汇总，人数是估计，月均现金工资单位埃镑、月均工时小时；不可作为 CBD、当前工资或法定最低工资。原表建筑业 190 小时，物理第 32 页英文摘要写 221 小时，存在冲突且原因未核，均保留；应查原刊抽样与定义。2025-06-02 建立目录，不能证明当前 PDF 与当时文件完全相同。'}
