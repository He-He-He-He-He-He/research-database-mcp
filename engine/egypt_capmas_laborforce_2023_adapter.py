"""Verified snapshot of CAPMAS 2024 labour force survey bulletin."""
import release_runtime
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import fitz
URL = 'https://metadata.capmas.gov.eg/ar/index.php/catalog/1894/download/6804'
CATALOG_URL = 'https://metadata.capmas.gov.eg/ar/index.php/catalog/1894'
SHA256 = '439685fae13dff16d212eb743df4e165084889144bd35352848de053f9fd467b'
PAGES = 263

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
    fd, tmp = tempfile.mkstemp(prefix='.capmas-laborforce-', suffix='.pdf', dir=path.parent)
    os.close(fd)
    try:
        try:
            release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '180', '--max-filesize', '40000000', '-o', tmp, URL], check=True, capture_output=True, timeout=185)
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
        raise ValueError('Physical page must be an integer between 1 and 263')
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as document:
        text = document[page_number - 1].get_text()
    return {'source': 'CAPMAS Annual Bulletin of Labour Force 2023', 'source_url': URL, 'catalog_url': CATALOG_URL, 'sha256': SHA256, 'physical_page': page_number, 'text': text, 'note': '文本抽取可能乱序、漏掉图片或合并单元格；须回看原 PDF 页面。原刊为劳动力家庭抽样调查；人数单位与年龄范围按原页定义，估计值不代表 CBD。目录创建于 2024-07-22；当前 PDF 与截止时版本是否完全相同未证实。'}

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
    return {'source': 'CAPMAS Annual Bulletin of Labour Force 2023', 'source_url': URL, 'sha256': SHA256, 'year': '2024', 'sex_physical_page': 39, 'road_user_physical_page': 43, 'sex_rows': [{'area_as_printed': n, **dict(zip(('male', 'female', 'total'), r))} for n, r in zip(areas, sex)], 'road_user_rows': [{'area_as_printed': n, **dict(zip(('pass_by_the_road_as_printed', 'driver', 'passenger', 'other_unknown', 'total'), r))} for n, r in zip(areas, users)], 'note': '道路事故死亡人数，不是事故数、风险率或 CBD 数据。省级分项包含在全国，性别与道路用户为同一人群不同维度，不可叠加；pass by the road 沿用原刊表述，具体道路使用者定义见原刊。目录于 2025-05-15 创建，不能证实当前 PDF 与当时完全同版。'}

def selected_2023(path):
    """Compare age-specific labels of Tables B and J and retain source cells."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as doc:
        p = doc[31]
        values = [p.get_textbox(fitz.Rect(246, y, 282, y + 14)).strip() for y in (266.5, 287.5, 308, 329.5, 350.5, 371, 392.5, 413.5, 434, 455.5, 476.5, 497)]
        atext = p.get_text()
        p = doc[39]
        bvalues = [p.get_textbox(fitz.Rect(a, 508, b, 522)).strip() for a, b in ((447, 471), (309, 339), (177, 200))]
        btext = p.get_text()
    expected = ['25570', '5579', '31149', '24374', '4585', '28959', '1196', '994', '2190', '4.7', '17.8', '7.0']
    if values != expected or bvalues != ['4.7', '17.8', '7.0'] or '15 years& above' not in atext or ('15-64years' not in btext):
        raise RuntimeError('Labour force tables differ from reviewed original')
    return {'source': 'CAPMAS Annual Bulletin of Labour Force 2023', 'source_url': URL, 'sha256': SHA256, 'year': '2023', 'table_b_physical_page': 32, 'table_j_physical_page': 40, 'table_b_age': '15 years and above', 'table_b_unit_counts': 'thousand persons', 'table_b_rows': [{'gender': name, 'labour_force_thousand': values[i], 'employed_thousand': values[i + 3], 'unemployed_thousand': values[i + 6], 'unemployment_rate_percent': values[i + 9]} for i, name in enumerate(('Male', 'Female', 'Total'))], 'table_j_age': '15–64 years', 'table_j_rate_percent': dict(zip(('Male', 'Female', 'Total'), bvalues)), 'note': '全国年度家庭调查估计，人数单位千人；失业率分母为对应年龄和性别劳动力，不是总人口。表 B 为 15 岁及以上，表 J 为 15–64 岁，数值虽相同但范围不同，不可互换；男女与合计重叠，数值保留原表四舍五入。非 CBD 数据；目录 2024-07-22 创建但当前 PDF 是否同版未证。'}

def participation_employment_2023(path):
    """Compare 15+ activity and employment rates with correct denominators."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as doc:
        p = doc[32]
        participation = [w[4] for w in p.get_text('words') if 299.8 < w[1] < 300.0 and w[4] in ('69.6', '15.9', '43.4')]
        t1 = p.get_text()
        p = doc[33]
        employment = [p.get_textbox(fitz.Rect(a, 487, b, 503)).strip() for a, b in ((448, 479), (303, 334), (159, 190))]
        t2 = p.get_text()
    if participation != ['69.6', '15.9', '43.4'] or employment != ['66.3', '13.1', '40.4'] or '15 years& above' not in t1 or ('15 years& above' not in t2):
        raise RuntimeError('Participation/employment tables differ from reviewed original')
    return {'source': 'CAPMAS Annual Bulletin of Labour Force 2023', 'source_url': URL, 'sha256': SHA256, 'year': '2023', 'age': '15 years and above', 'participation_physical_page': 33, 'employment_physical_page': 34, 'unit': 'percent', 'rows': [{'gender': g, 'economic_activity_rate': a, 'employment_rate': e} for g, a, e in zip(('Male', 'Female', 'Total'), participation, employment)], 'note': '经济活动率=劳动力/对应人口，就业率=就业人数/对应人口；人口均限定相应性别和 15 岁及以上。它们均不等同失业率（失业者/劳动力）。全国年度家庭调查估计，不代表 CBD；女性与男性率的差异不能直接判定原因。目录 2024-07-22 建立，当前 PDF 与当时版本完全一致未证。'}

def youth_unemployment_2023(path):
    """Table L youth 15–29 unemployment rate for 2023."""
    path = release_runtime.expandpath(Path(path))
    _verify(path)
    with fitz.open(path) as doc:
        p = doc[41]
        values = [p.get_textbox(fitz.Rect(a, 517, b, 533)).strip() for a, b in ((436, 469), (313, 346), (193, 226))]
        text = p.get_text()
    if values != ['10.7', '40.3', '15.9'] or '15-29 years' not in text:
        raise RuntimeError('Youth unemployment table differs from reviewed original')
    return {'source': 'CAPMAS Annual Bulletin of Labour Force 2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 42, 'printed_page': 35, 'table': 'L', 'year': '2023', 'age': '15–29 years', 'unit': 'percent', 'rates': dict(zip(('Male', 'Female', 'Total'), values)), 'note': '全国年度家庭调查估计，分母为相应性别 15–29 岁劳动力，而不是同年龄全部人口或 CBD 人口；失业率与就业率、劳动力参与率不可混同，不据性别差异单独推断原因。原目录 2024-07-22 建立，当前文件与当时同版未经证实。'}
