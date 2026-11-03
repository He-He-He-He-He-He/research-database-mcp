"""CAPMAS Egypt in Figures 2024, preserved official PDF snapshot."""
import release_runtime
import hashlib, os, subprocess, tempfile
from pathlib import Path
import fitz
URL = 'https://mediadr.sis.gov.eg/bitstream/handle/123456789/58352/CAPMAS20240300_005.pdf?isAllowed=y&sequence=1'
SHA256 = '94839f7e8fc7785dc0fca9c855125e5682e6efca3c0930d0c7536855f8ebe443'

def _hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def download(destination):
    path = release_runtime.expandpath(Path(destination))
    if path.exists():
        raise FileExistsError('Destination already exists')
    if not path.parent.is_dir():
        raise ValueError('Destination directory does not exist')
    fd, tmp = tempfile.mkstemp(prefix='.egypt-figures-', suffix='.pdf', dir=path.parent)
    os.close(fd)
    try:
        try:
            release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '120', '--max-filesize', '60000000', '-o', tmp, URL], check=True, capture_output=True, timeout=125)
        except (subprocess.SubprocessError, OSError) as e:
            raise RuntimeError('Official PDF download failed: ' + type(e).__name__) from None
        digest = _hash(tmp)
        if digest != SHA256:
            raise RuntimeError('PDF version hash differs from verified snapshot; inspect source before using')
        with fitz.open(tmp) as doc:
            if len(doc) != 230:
                raise RuntimeError('Unexpected PDF page count')
        os.link(tmp, path)
        return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'path': str(path.absolute()), 'bytes': path.stat().st_size, 'sha256': digest, 'pages': 230, 'note': '2024 版历史统计汇编，数字具体年份因表而异；请根据原 PDF 表头、注释、单位及统计期引用。'}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def _open_checked(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('Local file does not match verified CAPMAS 2024 snapshot')
    return fitz.open(path)

def page(path, number):
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 230):
        raise ValueError('PDF page must be 1–230')
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        text = doc[number - 1].get_text()
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': number, 'text': text, 'note': '物理页码从1开始，可能不同于印刷页码；PDF 文本表格列序及阿拉伯文可能错乱，图片文字未 OCR。必须回看原 PDF 页面和单位；2024出版不代表全部为2024年数据。'}

def airports(path):
    bounds = [(185, 235), (240, 265), (268, 307), (310, 348), (354, 380), (385, 420), (423, 452)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[106]
        rows = []
        for y in (477.8, 492.0):
            rows.append([p.get_textbox(fitz.Rect(left, y - 3, right, y + 11)).strip() for left, right in bounds])
    expected = [['Capital', '338.2', '149', '34', '2.9', '340', '92'], ['Total', '61.0', '38 211 514', '23 732 888', '46.3', '329 746', '225 462']]
    if rows != expected:
        raise RuntimeError('Airport table no longer matches visually verified snapshot')
    keys = ['airport', 'passenger_change_percent', 'passengers_2022', 'passengers_2021', 'aircraft_change_percent', 'aircraft_2022', 'aircraft_2021']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 107, 'printed_page': 93, 'rows': [dict(zip(keys, r)) for r in rows], 'note': '仅提取原表 Capital 和 Total 两行，值保留原样（空格为千位分隔）；是飞机及旅客流量，包含国际、国内、军用、私人及其他，旅客数非去重人数。Capital 为原表机场名称，不能直接等同 CBD 客流。CAPMAS 机场指标 API 中 2021 全国总量为 23768098，原刊表为 23732888，来源存在差异、原因未核，不擅自统一。原表 Capital 飞机数 2021 为 92、2022 为 340，变动率却标 2.9%，按数值计算约 269.6%；冲突原因未核，原样保留。'}

def new_companies(path):
    """Extract only the four visually verified totals of fiscal 2022/23."""
    bounds = [(140, 255), (270, 330), (345, 395)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[132]
        rows = []
        for y in (296.3, 406.6, 540.7, 558.8):
            rows.append([p.get_textbox(fitz.Rect(left, y - 3, right, y + 11)).strip() for left, right in bounds])
    expected = [['Total', '53 625.10', '13 976'], ['Total', '5 394.26', '74'], ['Total', '56 604.11', '18 413'], ['Total', '115 623.47', '32 463']]
    if rows != expected:
        raise RuntimeError('Company table differs from visually verified snapshot')
    labels = ['Internal Investment', 'Free Zones', 'Law 159', 'Grand Total']
    output = [{'category': label, 'printed_row_label': row[0], 'issued_capital_million_egp_original': row[1], 'companies_original': row[2]} for label, row in zip(labels, rows)]
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 133, 'printed_page': 117, 'original_source': 'General Authority of Investment and Free Zones', 'period': '2022-07-01 to 2023-06-30', 'rows': output, 'note': '仅提取四个已人工核图的总计行；原表统计依据投资法律在该期间新设公司，已发行资本单位为百万埃镑，数字空格是千位分隔。公司数不是全部存量或存活企业；已发行资本不等于实际到位资金、外国直接投资或 CBD 项目投资。总计与三个分项重叠，不能重复相加。'}

def gdp_selected(path):
    """Five visually verified industry rows at constant and current prices."""
    pages = [(123, 107, 'constant', [255.3, 391.1, 411.7, 552.8, 571.6]), (124, 108, 'current', [277.4, 403.5, 421.7, 557.7, 574.4])]
    expected = [[['Gross Domestic', '3.6', '7 726 764.2', '7 457 122.3'], ['Construction', '5.2', '598 405.1', '568 898.3'], ['Transportation & Storage', '4.3', '401 828.7', '385 388.0'], ['Hotels &Restaurants', '28.0', '225 717.6', '176 354.8'], ['Real Estate Activities', '3.8', '846 273.5', '815 085.9']], [['Gross Domestic Product', '29.4', '9 645 960.4', '7 457 122.3'], ['Construction', '40.0', '796 269.2', '568 898.3'], ['Transportation & Storage', '27.9', '492 892.3', '385 388.0'], ['Hotels &Restaurant', '70.4', '300 567.1', '176 354.8'], ['Real Estate Activities', '21.4', '989 531.3', '815 085.9']]]
    bounds = [(100, 200), (245, 280), (290, 355), (355, 425)]
    output = []
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        for idx, (physical, printed, price, ys) in enumerate(pages):
            page = doc[physical - 1]
            rows = []
            for y in ys:
                rows.append([page.get_textbox(fitz.Rect(left, y - 3, right, y + 11)).strip() for left, right in bounds])
            if rows != expected[idx]:
                raise RuntimeError('GDP table differs from visually verified snapshot')
            for label, row in zip(('GDP', 'Construction', 'Transportation & Storage', 'Hotels & Restaurants', 'Real Estate Activities'), rows):
                output.append({'price_basis': price, 'physical_page': physical, 'printed_page': printed, 'sector': label, 'source_label_fragment': row[0], 'growth_percent_original': row[1], 'fy_2022_2023_million_egp_original': row[2], 'fy_2021_2022_million_egp_original': row[3]})
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'original_source': 'Ministry of Planning and Economic Development', 'rows': output, 'note': 'GDP 按要素成本，单位百万埃镑；恒价基年为2021/22，现价与恒价不可混同。仅提取五个已核图行业及总量，分项属总量一部分；原表 2022/23 带星号，其含义在本页未说明，勿自行推断。统计为历史版本、可修订，不是 CBD 项目业绩。'}

def inflation_check(path):
    """Compare visually verified monthly CPI and annual inflation source pages."""
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[143]
        bounds = [(170, 200), (215, 245), (250, 280), (290, 320), (325, 355)]
        table = [[p.get_textbox(fitz.Rect(a, y - 3, b, y + 11)).strip() for a, b in bounds] for y in (242.5, 484.0)]
        p = doc[145]
        annual = [[p.get_textbox(fitz.Rect(a, y - 3, b, y + 11)).strip() for a, b in ((210, 250), (300, 330))] for y in (337.3, 353.8)]
    if table != [['Jan.', '4.7', '148.7', '7.3', '118.1'], ['Annual\nAverage', '2.5', '173.3', '13.9', '129.5']] or annual != [['13.9', '2022'], ['33.9', '2023']]:
        raise RuntimeError('CPI table differs from visually verified snapshot')
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'monthly_table_physical_page': 144, 'monthly_table_printed_page': 126, 'annual_table_physical_page': 146, 'annual_table_printed_page': 128, 'index_base': '2018/2019=100', 'monthly_rows': [{'label': row[0], '2023_rate_of_change_percent_as_printed': row[1], '2023_cpi_index': row[2], '2022_rate_of_change_percent_as_printed': row[3], '2022_cpi_index': row[4]} for row in table], 'annual_inflation_rows': [{'year': row[1], 'annual_inflation_percent_as_printed': row[0]} for row in annual], 'note': '仅抽取已核图的1月与年度平均示例和2022/2023年度通胀两行，城镇CPI指数基期2018/19=100。原刊第126页脚注称变动率为同比，但2023年1月148.7与2022年1月118.1计算约25.9%，表中却为4.7%；同页2023年年度平均变动率2.5%，第128页年度通胀为33.9%。原文存在不一致，不能擅自认定哪一列或定义正确，须向CAPMAS核实。年度平均和月度不可混同，非当前通胀或CBD租金。'}

def population_selected(path):
    pages = [(11, 4, '2024-01-01', [166.1, 329.8, 508.0], [(190, 250), (265, 320), (325, 380), (385, 440)]), (15, 8, '2023-07-01', [175.4, 328.3, 494.1], [(185, 240), (315, 375), (378, 420), (425, 465)])]
    expected = [[['Cairo', '10 299 821', '4 992 277', '5 307 544'], ['Giza', '9 578 680', '4 626 889', '4 951 791'], ['Total', '105 914 499', '51 472 894', '54 441 605']], [['Cairo', '10 248 385', '4 964 049', '5 284 336'], ['Giza', '9 514 540', '4 594 135', '4 920 405'], ['Total', '105 174 090', '51 100 307', '54 073 783']]]
    output = []
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        for i, (physical, printed, date, ys, bounds) in enumerate(pages):
            p = doc[physical - 1]
            rows = [[p.get_textbox(fitz.Rect(a, y - 3, b, y + 11)).strip() for a, b in bounds] for y in ys]
            if rows != expected[i]:
                raise RuntimeError('Population table differs from visually verified snapshot')
            for row in rows:
                output.append({'date': date, 'physical_page': physical, 'printed_page': printed, 'area_as_printed': row[0], 'total_original': row[1], 'female_original': row[2], 'male_original': row[3]})
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'unit': 'persons', 'rows': output, 'note': '仅抽取已核图的 Cairo、Giza 省及全国 Total，日期为各表人口估计时点；全国与省级重叠，不能将总计与分项相加。原表标题为人口估计，脚注又称总人口 based on natural increasing，原文并存，不应将其称为逐人普查实数。两时点相隔半年，不是年度增长率；开罗省和吉萨省也不是新行政首都或 CBD 人口。'}

def electricity_selected(path):
    bounds = [(180, 275), (295, 330), (350, 402), (410, 453)]
    ys = (177, 189.2, 201.2, 250, 262.2)
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[90]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 10)).strip() for a, b in bounds] for y in ys]
    expected = [['Generated Electricity', '4.6', '214 220', '204 794'], ['Sold Electricity', '6.4', '163 985', '154 176'], ['Industry', '8.5', '45 701', '42 123'], ['Houses', '0.8', '62 912', '62 393'], ['Shops & Other', '13.5', '22 720', '20 022']]
    if rows != expected:
        raise RuntimeError('Electricity table differs from visually verified snapshot')
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 91, 'printed_page': 79, 'unit_as_printed': 'GW/h', 'rows': [{'item': r[0], 'change_percent_original': r[1], 'fy_2021_2022_original': r[2], 'fy_2020_2021_original': r[3]} for r in rows], 'note': '仅提取原表发电、售电及工业、住户、商店与其他三类已核图行，行业项属于售电分项，不能与售电总量相加。原表单位印为 GW/h，与电能常见的 GWh 表述存在歧义，原样保留，换算前须核官方原始说明；发电与售电差额不能直接认定为线损。全国历史财年资料不代表新首都 CBD 能源中心的供电或消费。'}

def housing_levels(path):
    """Extract the visually checked national housing table, preserving strings."""
    bounds = [(178, 225), (230, 280), (282, 325), (328, 365), (370, 404), (407, 439), (441, 462)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[94]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (214, 231.5, 247.3, 264.6, 282.6, 301.5)]
    expected = [['Low Cost', '360900', '360900', '0', '802', '802', '0'], ['Economic', '75 876 820', '18 116 100', '57 760 720', '88 408', '40 258', '48 150'], ['Middle', '35 385 427', '25 364 600', '10 020 827', '49 801', '39 833', '9 968'], ['Upper Middle', '11 373 447', '6 281 100', '5092347', '8 053', '7 666', '387'], ['Luxury', '64 604 755', '47 366 100', '17238655', '31 804', '29 749', '2055'], ['Total', '187 601 349', '97 488 800', '90 112 549', '178 868', '118 308', '60 560']]
    if rows != expected:
        raise RuntimeError('Housing table differs from visually verified snapshot')
    keys = ['cost_level', 'investment_total_original', 'investment_private_original', 'investment_public_original', 'housing_units_total_original', 'housing_units_private_original', 'housing_units_public_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 95, 'printed_page': 82, 'underlying_source': 'Ministry of Housing, Utilities & Urban Development', 'period_as_printed': '22/2023', 'unit_housing': 'number', 'unit_investment_as_printed': '000 L.E.', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表全国数据按住房成本级别及公私部门分列，总计与分项重叠不可相加；投资额不包含住宅单价，而是最近结算所涉工程价值，私人部门投资额不含土地价格及公用设施成本，原刊英文与阿拉伯文脚注须结合原页核验。统计时点和单位完成状态须核来源，不能视为住房售价、租金、CBD 住宅或新首都数据。'}

def housing_permits(path):
    """Extract 2020–22 national permits, with absent non-housing 2020 kept null."""
    bounds = [(250, 280), (283, 311), (312, 348), (352, 395), (410, 439)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[95]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (185.6, 203.6, 218.4)]
        labels = [p.get_textbox(fitz.Rect(180, a, 240, b)).strip() for a, b in ((180, 201), (203, 215), (217, 230))]
    if rows != [['710', '1380', '2545', '1460', '1076'], ['2939', '5655', '113818', '159965', '40879'], ['3649', '7035', '116363', '161425', '41955']] or labels != ['Public & \nGovernmental', 'Private', 'Total']:
        raise RuntimeError('Permits table differs from visually verified snapshot')
    result = []
    for label, row in zip(labels, rows):
        result.append({'sector_as_printed': label, 'non_housing_2022_original': row[0], 'non_housing_2021_original': row[1], 'non_housing_2020_original': None, 'housing_2022_original': row[2], 'housing_2021_original': row[3], 'housing_2020_original': row[4]})
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 96, 'printed_page': 83, 'unit_as_printed': 'No.', 'title_as_printed': 'Housing & non Housing Permits Units By Sector (2020-2022)', 'rows': result, 'note': '原表非住宅只列 2021 和 2022，2020 为未提供而非零；住宅与非住宅为建筑许可数据，不代表已完工、投入使用或住宅市场成交。表中部门分项与总计重叠，不能相加；表格全国历史口径不是新首都 CBD 许可或规模。原刊英语与阿拉伯语对许可对象的建筑/单元措辞需核原页，不能据此推导实际建筑或住宅套数。'}

def social_housing_selected(path):
    """Extract three reviewed rows in the national social housing program table."""
    bounds = [(193, 244), (251, 282), (287, 316), (323, 351), (359, 386), (396, 421), (430, 456)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[97]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 10)).strip() for a, b in bounds] for y in (283.6, 383.2, 450.3)]
    expected = [['Cairo', '82 938', '10 284', '0', '0', '0', '0'], ['Giza', '69 396', '14 184', '0', '0', '0', '0'], ['Total', '230 624', '42 472', '2 779', '4 055', '201', '580']]
    if rows != expected:
        raise RuntimeError('Social housing table differs from visually verified snapshot')
    keys = ['governorate', 'new_communities_under_implementation_original', 'new_communities_implemented_original', 'housing_directorates_under_implementation_original', 'housing_directorates_implemented_original', 'central_reconstruction_under_implementation_original', 'central_reconstruction_implemented_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 98, 'printed_page': 85, 'period_as_printed': '2022/2023', 'unit_as_printed': 'No.', 'rows': [dict(zip(keys, row)) for row in rows], 'note': '仅抽取社会住房项目表中的开罗省、吉萨省和全国总计；各机构实施中与已实施为不同状态，不能将实施中等同完工。原表标题提到投资，但页面无投资数值，不能据此推导金额。表中全国总计与省分项重叠，不能重复相加；省级社会住房不代表新行政首都 CBD 公寓。原表数字按财年标示，不说明是否为累计数，不能推断。'}

def balance_of_payments_selected(path):
    bounds = [(125, 280), (289, 325), (338, 375)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[124]
        rows = [[p.get_textbox(fitz.Rect(a, y - 1, b, y + 11)).strip() for a, b in bounds] for y in (159.4, 252.8, 299.4, 516.9, 582.6)]
    expected = [['Trade Balance', '-31159.6', '-43396.0'], ['Services Balance', '21926.5', '11158.7'], ['Travel (tourism revenues)', '13629.3', '10748.1'], ['Balance of Current Account', '-4710.5', '-16551.3'], ['Direct investment in Egypt(net)(2)', '10038.6', '8937.4']]
    if rows != expected:
        raise RuntimeError('Balance of payments table differs from visually verified snapshot')
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Central Bank of Egypt', 'source_url': URL, 'sha256': SHA256, 'physical_page': 125, 'printed_page': 109, 'footnotes_physical_page': 126, 'unit_as_printed': 'Mil .US$', 'periods_as_printed': ['*2023/22', '*2022/21'], 'rows': [{'item_as_printed': r[0], 'fy_2022_2023_original': r[1], 'fy_2021_2022_original': r[2]} for r in rows], 'note': '原刊收支平衡表，日期为财年、两列均带星号，星号含义未在本页或续页找到；保留原值与正负号，不将净额解释为流入总额。旅游收入属服务收款分项，不能与服务余额或经常账户余额相加；不是酒店收入或 CBD 招商。续页脚注：直接投资及收益的编制自2018/19第一季度采用新方法，包括所有未分配已实现收益，既往仅包括再投资收益。全国历史资料可能修订，非实时数据。'}

def vehicles_selected(path):
    bounds = [(185, 245), (278, 316), (336, 373), (393, 438)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[99]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 10)).strip() for a, b in bounds] for y in (183.1, 214.5, 286.6, 299.7, 312.8, 496.3, 523.6)]
    expected = [['Private', '5 229 787', '5 111 892', '5 021 762'], ['Taxi', '310 255', '327 979', '347 880'], ['Public', '12 797', '13 776', '15 232'], ['Private', '76 694', '79 819', '80 631'], ['Tourism', '19 545', '19 360', '20 825'], ['Motorcycles', '2646 791', '2 694 784', '3 559 632'], ['Total', '9 945 052', '9 941 266', '10 909 456']]
    if rows != expected:
        raise RuntimeError('Vehicle table differs from visually verified snapshot')
    groups = ['Cars', 'Cars', 'Bus', 'Bus', 'Bus', 'Others', 'Total']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'General Traffic Department', 'source_url': URL, 'sha256': SHA256, 'physical_page': 100, 'printed_page': 86, 'unit_as_printed': 'No.', 'date_as_printed': 'Up to end of Dec.', 'years_as_printed': ['*2023', '2022', '2021'], 'rows': [{'group_as_printed': g, 'item_as_printed': r[0], 'year_2023_original': r[1], 'year_2022_original': r[2], 'year_2021_original': r[3]} for g, r in zip(groups, rows)], 'note': '原表为截至各年12月底在用持牌车辆，2023 带星号，原页未说明含义；选行归属保留以区分汽车 Private 和巴士 Private。总计与分项重叠，不可相加；全国历史车辆存量不是年度新增、车辆流量、CBD 停车需求或当前保有量。'}

def communications_services(path):
    spans = [(263, 285, 268.7), (319, 341, 324.3), (379, 390, 379.9), (435, 446, 435.6), (485, 507, 491.2)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[115]
        rows = []
        for top, bottom, y in spans:
            rows.append([p.get_textbox(fitz.Rect(a, top, b, bottom)).strip() for a, b in ((185, 278), (283, 305))] + [p.get_textbox(fitz.Rect(a, y - 1, b, y + 11)).strip() for a, b in ((315, 340), (348, 375), (385, 410))])
    expected = [['Total Capacity of Local \nExchange', 'Mil.\n Line', '-3.8', '20.98', '21.81'], ['Fixed Tel. Lines \nSubscribers', 'Mil.\nSub.', '7.7', '12.48', '11.59'], ['Cellular Phone Subscribers', 'Mil', '6.9', '106.21', '99.38'], ['Exchanges in Rural', 'No.', '...', '...', '1072'], ['ADSL High Speed Internet \nSubscribers', 'Mil.\nSub.', '...', '...', '11.04']]
    if rows != expected:
        raise RuntimeError('Communications table differs from visually verified snapshot')
    keys = ['item_as_printed', 'unit_as_printed', 'change_percent_as_printed', 'december_2023_as_printed', 'december_2022_as_printed']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Communications & Information Technology', 'source_url': URL, 'sha256': SHA256, 'physical_page': 116, 'printed_page': 101, 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表为全国2022和2023年12月通信服务，行内单位各异。省略号为原始缺失标记，非零；移动电话计量为线路/订阅，不等于独立用户人数，ADSL 不代表全部宽带。全国历史数据不能作为 CBD 网络质量、接入率或用户数。'}

def unemployment_selected(path):
    bounds = [(185, 258), (282, 311), (354, 381), (417, 440)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[60]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (180.6, 343.6, 495.9, 525.8)]
    expected = [['Cairo', '10.5', '18.8', '8.4'], ['Giza', '9.9', '26.3', '6.9'], ['North Sinai', '', '', ''], ['Egypt Rate', '7.0', '17.8', '4.7']]
    if rows != expected:
        raise RuntimeError('Unemployment table differs from visually verified snapshot')
    keys = ['area_as_printed', 'total_percent_as_printed', 'female_percent_as_printed', 'male_percent_as_printed']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 61, 'printed_page': 51, 'year_as_printed': '2023*', 'age_as_printed': '15–64 years', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表为 15–64 岁失业率，分性别数值不是全部人口的比例，不可相加；原表 North Sinai 数值空白保留空字符串，不等于零。2023 星号本页未解释；Cairo、Giza 是省级统计，非新行政首都或 CBD 的用工、失业或招聘数据。'}

def employed_selected(path):
    bounds = [(185, 258), (282, 320), (349, 382), (402, 442)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[58]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (177.3, 348.6, 506.7, 533.5)]
    expected = [['Cairo', '25 930', '4 814', '21 116'], ['Giza', '25 510', '3 185', '22 324'], ['North Sinai', '-', '-', '-'], ['Total', '289 591', '45 846', '243 744']]
    if rows != expected:
        raise RuntimeError('Employment table differs from visually verified snapshot')
    keys = ['area_as_printed', 'total_original', 'female_original', 'male_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 59, 'printed_page': 49, 'year_as_printed': '2023*', 'age_as_printed': '15 years old and over', 'unit_as_printed': '00', 'arabic_unit_as_printed': 'ﺑﺎﻟﻤﺌﺎت', 'unit_interpretation': 'hundreds of persons', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表为15岁及以上就业人数估计，单位百人，保留原数及 North Sinai 短横线，不视为零；2023 星号本页未解释。Giza 男女分项相加与原总数差1个原始单位，全国也差1，原因未知，不能自行修正。失业率原表限定15–64岁，与此表年龄范围不同，不能简单合并计算失业率。省级不是 CBD 人员或招聘。'}

def internet_subscriptions_selected(path):
    bounds = [(188, 232), (238, 257), (260, 283), (289, 312), (319, 343), (345, 370), (373, 397), (402, 427), (429, 454), (456, 480)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[118]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (246.5, 390.7, 411.3, 473.1)]
    expected = [['January', '9.3', '12.4', '9.58', '11.13', '2.53', '69.52', '10.18', '2.25', '63.44'], ['August', '9.9', '-22.2', '6.91', '11.75', '1.58', '74.57', '10.69', '2.03', '69.75'], ['September', '-', '19.8', '8.30', '-', '2.42', '75.51', '10.77', '2.02', '69.72'], ['December', '-', '-', '11.00', '-', '-', '76.68', '11.04', '2.42', '69.08']]
    if rows != expected:
        raise RuntimeError('Internet subscriptions table differs from visually verified snapshot')
    keys = ['month_as_printed', 'adsl_change_percent', 'usb_change_percent', 'mobile_change_percent', 'adsl_2023', 'usb_2023', 'mobile_2023', 'adsl_2022', 'usb_2022', 'mobile_2022']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Communication and IT', 'source_url': URL, 'sha256': SHA256, 'physical_page': 119, 'printed_page': 104, 'title_as_printed': 'Number of Internet Subscriptions (2022-2023)', 'unit_as_printed': 'Mil. Users', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '仅抽取已核图的1、8、9、12月，原题为互联网订阅数，而单位写 Mil. Users，两种措辞并存，不将其解释为去重用户人数。原表短横线表示未提供，不是零；变动率、订阅数据是不同单位，ADSL、USB、移动订阅用户可能重叠，不能直接相加为人数。全国历史数据不等于 CBD 接入或质量。'}

def fuel_emissions_selected(path):
    bounds = [(162, 252), (300, 325), (359, 397)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[223]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (225.9, 239.3, 266.1, 279.5, 335.2)]
        chart = p.get_textbox(fitz.Rect(459, 406, 480, 416)).strip()
    expected = [['Manufacturing', '23.8', '13550.6'], ['Transport  (Vehicle)', '63.0', '20318.8'], ['Housing / Commercial', '17.7', '6181.2'], ['Electricity', '85.0', '31001'], ['Total', '208.0', '79653.6']]
    if rows != expected or chart != '63.01':
        raise RuntimeError('Fuel emissions table differs from visually verified snapshot')
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Petroleum and Mineral Resources', 'source_url': URL, 'sha256': SHA256, 'physical_page': 224, 'printed_page': 199, 'period_as_printed': '21/2022', 'fuel_consumption_unit_as_printed': '000 Tons', 'co2_emissions_unit_as_printed': 'Mill Tons', 'rows': [{'sector_as_printed': r[0], 'co2_emissions_original': r[1], 'fuel_consumption_original': r[2]} for r in rows], 'transport_chart_value_as_printed': chart, 'note': '仅原表已核图五行。石油产品与天然气消费为千吨，其导致的 CO2 排放为百万吨，不可混合单位；表内运输排放63.0、同页图示63.01，精度不同或原因未核，均保留。总计与行业分项重叠，不能重复相加；不是全温室气体 CO2 当量或 CBD 本身排放。'}

def employed_industries_selected(path):
    bounds = [(185, 292), (299, 318), (324, 352), (358, 383), (386, 416)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[57]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.7, b, y + 8.6)).strip() for a, b in bounds] for y in (268.5, 306.4, 316.4, 327, 338.3, 349.5, 528.9)]
    expected = [['Constructions', '14.2', '41 072', '231', '40 841'], ['Transportation , Storage', '9.3', '27 001', '351', '26 651'], ['Accommodation & Food Services', '3.4', '9 967', '457', '9 510'], ['Information & Communications', '0.8', '2 218', '414', '1 804'], ['Financial& Insurance Activities', '0.8', '2 279', '599', '1 680'], ['Real estate activity & Renting', '0.3', '747', '122', '625'], ['Total', '100', '289 591', '45 846', '243 744']]
    if rows != expected:
        raise RuntimeError('Employment industry table differs from visually verified snapshot')
    keys = ['industry_as_printed', 'share_percent_as_printed', 'total_original', 'female_original', 'male_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 58, 'printed_page': 48, 'year_as_printed': '2023*', 'age_as_printed': '15 years old and over', 'unit_as_printed': '00', 'unit_interpretation': 'hundreds of persons', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '所选全国行业就业人数为15岁及以上估计，原文数值单位百人，百分比为行业占全部就业者比例而非女性占比。交通分项的男女原值相加与总值差一个原始单位，全国合计亦差一个，原因未知。2023 星号本页未释义；总计与行业分项重叠，不可相加；不是 CBD 行业就业人数。全国总计与同刊第49页分省表一致。'}

def company_capital_increases_selected(path):
    bounds = [(145, 220), (222, 268), (279, 317), (327, 365), (383, 426)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[135]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.7, b, y + 10)).strip() for a, b in bounds] for y in (277.5, 307.3, 322.3, 337.2, 391.9)]
        raw = p.get_text()
    expected = [['Services', '53 301.90', '5 512.14', '1 241.18', '46 548.58'], ['Finance', '28 331.47', '9 029.89', '10 300.95', '9 000.63'], ['Constructional', '18 115.59', '515.90', '500.48', '17 099.21'], ['Tourism', '5 192.58', '392.08', '700.41', '4 100.09'], ['Total', '129 672.4', '23 601.85', '16 233.35', '89 837.17']]
    if rows != expected or not all((x in raw for x in ('0.2%', '0.3%', '12.5%', '[CATEGORY'))):
        raise RuntimeError('Capital increase table differs from visually verified snapshot')
    keys = ['industry_as_printed', 'total_original', 'foreigners_original', 'arabs_original', 'egyptians_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'General Authority for Investment & Free Zones', 'source_url': URL, 'sha256': SHA256, 'physical_page': 136, 'printed_page': 120, 'period_as_printed': '1/7/2022 - 30/6/2023', 'unit_as_printed': 'Mil . L.E.', 'rows': [dict(zip(keys, r)) for r in rows], 'chart_values_as_printed': ['0.2%', '12.5%', '0.3%'], 'note': '原表为依投资法律设立公司在该期的已发行资本增加，非当期新设公司已发行资本、实缴金额或外商直接投资。按表总计算外国和埃及类别约18.2%和69.3%，但同页饼图用 [CATEGORY NAME] 占位并分别显示0.2%和0.3%，图表与表格存在差异，原因未知，不自行更正；阿拉伯与外国为原表类别，分类边界须核原始定义。金额为百万埃镑，总额与行业及出资类别重叠，不能重复累加；非 CBD 投资。'}

def household_expenditure_selected(path):
    specs = [(149, [(179.3, 179.3, 190), (226.5, 230.5, 240), (281.8, 281.8, 292), (331.6, 331.6, 342), (361.1, 361.1, 372), (452.3, 452.3, 463)], [(300, 339), (340, 379), (380, 419)]), (150, [(188.5, 188.8, 199), (235.7, 240, 249), (291, 291.3, 301), (340.8, 341.1, 351), (369.1, 369.1, 379), (447.3, 447.3, 458)], [(305, 333), (335, 359), (362, 388)])]
    expected = [[['Food and Non - Alcoholic Beverages', '19229.3', '18822.4', '19743.4'], ['Housing, Water, Electricity, Gas & \nOther Fuels', '11890.6', '9758.2', '14584.9'], ['Transport', '4171.0', '3108.5', '5513.4'], ['Restaurants & Hotels', '2948.9', '2293.2', '3777.4'], ['Total Actual Consumption', '62625.0', '55211.1', '71992.6'], ['Total  Households Expenditure', '61907.4', '54452.1', '71327.5']], [['Food and Non - Alcoholic Beverages', '31.1', '34.6', '27.7'], ['Housing, Water, Electricity, Gas & Other \nFuels', '19.2', '17.9', '20.4'], ['Transport', '6.7', '5.7', '7.7'], ['Restaurants & Hotels', '4.8', '4.2', '5.3'], ['Total Actual Consumption', '101.2', '101.4', '100.9'], ['Total  Households Expenditure', '100.0', '100.0', '100.0']]]
    allrows = []
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        for idx, (physical, spans, bounds) in enumerate(specs):
            p = doc[physical - 1]
            rows = []
            for top, y, bottom in spans:
                rows.append([p.get_textbox(fitz.Rect(187, top - 0.7, 302, bottom)).strip()] + [p.get_textbox(fitz.Rect(a, y - 0.7, b, y + 9)).strip() for a, b in bounds])
            if rows != expected[idx]:
                raise RuntimeError('Household expenditure table differs from visually verified snapshot')
            allrows.append(rows)
    keys = ['item_as_printed', 'total_original', 'rural_original', 'urban_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'amount_physical_page': 149, 'amount_printed_page': 130, 'percentage_physical_page': 150, 'percentage_printed_page': 131, 'period_as_printed': '2019/2020', 'amount_unit_as_printed': 'L.E.', 'percentage_unit': '%', 'amount_rows': [dict(zip(keys, r)) for r in allrows[0]], 'percentage_rows': [dict(zip(keys, r)) for r in allrows[1]], 'note': '原刊金额页阿文标题称家庭年支出，比例页英文标题称人均年支出，措辞不一致，须核原始调查定义，勿将金额擅称人均。两表全国住房等11890.6与家庭总支出61907.4之比约19.2%，与比例表一致，但这是对照推算，不代替官方方法说明。实际消费101.2%超过家庭总支出100%，原刊脚注称实际消费包含实物、配给卡和面包转移；保留层级与原值，勿简单相加。2019/20历史家庭调查不等于现行消费或CBD租户收入。'}

def cpi_groups_selected(path):
    spans = [(210, 210.7, 222), (235, 240.3, 255), (307, 312.1, 327), (388, 393.1, 408), (419, 419.2, 430), (492, 491.8, 503)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[144]
        rows = []
        for top, y, bottom in spans:
            rows.append([p.get_textbox(fitz.Rect(185, top - 0.7, 285, bottom)).strip()] + [p.get_textbox(fitz.Rect(a, y - 0.7, b, y + 10)).strip() for a, b in [(289, 320), (327, 358), (366, 396), (404, 435)]])
    expected = [['All Items', '177.4', '131.0', '114.0', '107.8'], ['Food and Non - Al Coholic \nbeverages', '214.1', '130.9', '104.6', '99.4'], ['Housing, water, electricity , \nGas and  Other fuels', '130.5', '121.5', '114.2', '109.2'], ['Transport \n& Transportations', '161.3', '136.3', '122.4', '116.4'], ['Communications', '106.1', '104.6', '103.9', '103.4'], ['Restaurants  & Hotels', '202.5', '138.0', '115.8', '112.2']]
    if rows != expected:
        raise RuntimeError('CPI groups table differs from visually verified snapshot')
    keys = ['item_as_printed', 'year_2023_original', 'year_2022_original', 'year_2021_original', 'year_2020_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 145, 'printed_page': 127, 'base_as_printed': '2018/2019=100', 'coverage_as_printed': 'Egypt total (Arabic heading)', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表为全国各组消费价格指数，原页按年列值但未说明年均或年末；指数不是年度通胀百分比、价格金额、CBD 租金或项目费率。上一页城镇 CPI 2023 年均为173.3、本页全国总指数为177.4，地理范围不同、取样时点关系未核，不能视作矛盾或直接混同。总指数及各分项不应相加，实际通胀率须确认时点后计算。'}

def collected_garbage_selected(path):
    bounds = [(182, 235), (325, 370)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[224]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 8.4)).strip() for a, b in bounds] for y in (197.4, 211.2, 370.9)]
    expected = [['Total', '21 162 941'], ['Cairo', '5 605 443'], ['Giza', '2 584 639']]
    if rows != expected:
        raise RuntimeError('Collected garbage table differs from visually verified snapshot')
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 225, 'printed_page': 200, 'year_as_printed': '2022', 'unit_as_printed': 'Ton', 'rows': [{'area_as_printed': r[0], 'collected_garbage_original': r[1]} for r in rows], 'note': '原表2022年按省已收集垃圾量，单位吨；总数与省行重叠，不可相加。另一个 CAPMAS API 的市政垃圾指标是产生量且单位吨/日，统计对象与单位不同，不能未经核对推算收集率或直接比较；省级历史资料非 CBD 垃圾量。'}

def hospitals_selected(path):
    bounds = [(190, 235), (250, 266), (276, 295), (308, 325), (331, 353), (360, 384), (388, 414), (417, 446), (449, 468)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[188]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.4, b, y + 8.4)).strip() for a, b in bounds] for y in (214, 342.4, 491.6)]
        national = doc[187].get_textbox(fitz.Rect(420, 263.6, 445, 273)).strip()
    expected = [['Cairo', '…', '…', '…', '104', '71.3', '356', '254', '102'], ['Giza', '…', '…', '…', '35', '77.4', '155', '120', '35'], ['Total', '…', '…', '…', '655', '63.3', '1809', '1 145', '664']]
    if rows != expected or national != '662':
        raise RuntimeError('Hospitals table differs from visually verified snapshot')
    keys = ['area_as_printed', 'private_share_2022', 'total_2022', 'private_2022', 'government_2022', 'private_share_2021', 'total_2021', 'private_2021', 'government_2021']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Health and Population', 'source_url': URL, 'sha256': SHA256, 'physical_page': 189, 'printed_page': 167, 'national_series_physical_page': 188, 'unit_as_printed': 'No.', 'year_2022_as_printed': '2022*', 'rows': [dict(zip(keys, r)) for r in rows], 'national_government_hospitals_2022_other_table': national, 'note': '原表省级和总计2022年私人、总数和占比均为省略号，不能当零；原刊注私人医疗机构包含在2022/23经济普查中，不能据此填补缺值。省级表政府医院合计655，上一页全国行业表政府医院662，两表有差异且口径未核，不自行更正。2021政府664与 CAPMAS API 23/42/7349 回读一致，但该API实测无2022。星号未释义；Cairo/Giza非CBD医疗设施。'}

def hospital_beds_selected(path):
    bounds = [(185, 232), (240, 263), (272, 295), (303, 321), (327, 352), (358, 384), (388, 415), (421, 448), (449, 478)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[189]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.4, b, y + 8.5)).strip() for a, b in bounds] for y in (220.6, 358.2, 506.6)]
        other = doc[187].get_textbox(fitz.Rect(227, 442, 250, 452)).strip()
    expected = [['Cairo', '…', '…', '…', '19914', '32.5', '26797', '8702', '18095'], ['Giza', '…', '…', '…', '3951', '46.2', '7225', '3338', '3887'], ['Total', '…', '…', '…', '88427', '728.73', '117504', '34470', '83034']]
    if rows != expected or other != '29.3':
        raise RuntimeError('Hospital beds table differs from visually verified snapshot')
    keys = ['area_as_printed', 'private_share_2022', 'total_2022', 'private_2022', 'government_2022', 'private_share_2021', 'total_2021', 'private_2021', 'government_2021']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Health and Population', 'source_url': URL, 'sha256': SHA256, 'physical_page': 190, 'printed_page': 168, 'national_series_physical_page': 188, 'unit_as_printed': 'No.', 'year_2022_as_printed': '2022*', 'rows': [dict(zip(keys, r)) for r in rows], 'national_private_share_2021_other_table': other, 'note': '2022私人床位及总数为原表省略号，不是零；2021全国私人床位占比本页印728.73%，全国表印29.3%，且34470/117504约29.3%，存在冲突，原因未知不自行更正。2022政府床位合计88427与同刊全国表一致；2021政府83034与 CAPMAS API 23/42/7376 回读一致，接口未返回2022。星号未释义；床位数量不反映可用床位、医疗质量或 CBD 配套。'}

def water_balance_selected(path):
    spans = [(196.9, 196.5, 206), (276.1, 275.6, 285), (377.3, 376.8, 386), (399.6, 399.6, 409), (445.1, 444.7, 454), (463.3, 463, 472), (481.6, 481.2, 490), (515.8, 520.6, 536)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[227]
        rows = []
        for top, y, bottom in spans:
            rows.append([p.get_textbox(fitz.Rect(170, top - 0.7, 280, bottom)).strip()] + [p.get_textbox(fitz.Rect(a, y - 0.7, b, y + 9)).strip() for a, b in ((283, 313), (324, 355), (365, 396), (406, 436))])
    expected = [['Nile water', '55.50', '55.50', '55.50', '55.50'], ['Total fresh water resources', '59.68', '59.68', '59.28', '59.68'], ['Total reuse', '21.95', '26.26', '27.38', '25.82'], ['Total Water Resources', '81.63', '85.94', '86.66', '85.50'], ['For Drinking', '11.48', '11.48', '11.52', '11.53'], ['For Industry', '5.52', '5.52', '5.4', '5.4'], ['For Agricultural', '62.13', '61.87', '62.01', '61.63'], ['Total uses of Water \nResources', '81.63', '81.37', '81.43', '81.06']]
    if rows != expected:
        raise RuntimeError('Water balance table differs from visually verified snapshot')
    keys = ['item_as_printed', 'fy_2022_2023_original', 'fy_2021_2022_original', 'fy_2020_2021_original', 'fy_2019_2020_original']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'underlying_source': 'Ministry of Water Resources & Irrigation', 'source_url': URL, 'sha256': SHA256, 'physical_page': 228, 'printed_page': 202, 'unit_as_printed': 'Billion m3 / Year', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '全国水资源平衡表，原表总资源包含淡水和再利用，不能称作独立可再生淡水量；总数与分项重叠，不能重复相加。2021/22资源总量85.94与用途总量81.37不同，原因原页未说明，不推断缺口或自动调整；2022/23饮用水用途11.48与另一供水年报产量11.2875十亿立方米口径未核，不能直接比较。历史全国资料非 CBD 水源或实际消费。'}

def water_production_selected(path):
    bounds = [(188, 245), (260, 301), (313, 353), (372, 412), (419, 454)]
    with _open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[228]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 8.5)).strip() for a, b in bounds] for y in (187.3, 309.3, 467.5)]
        raw = p.get_text()
    expected = [['Cairo', '11.4', '1853.3', '10.3', '1864.7'], ['Giza', '0.8', '1486.3', '1.6', '1497.7'], ['Total Egypt', '12.2', '11 167', '11.9', '10 992']]
    if rows != expected or 'Used to irrigate gardens and roads' not in raw:
        raise RuntimeError('Water production table differs from visually verified snapshot')
    keys = ['area_as_printed', 'non_refined_2021_2022', 'refined_2021_2022', 'non_refined_2020_2021', 'refined_2020_2021']
    return {'source': 'CAPMAS Egypt in Figures 2024 via Egypt State Information Service', 'source_url': URL, 'sha256': SHA256, 'physical_page': 229, 'printed_page': 203, 'unit_as_printed': 'MIL. M3', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表2020/21、2021/22按省水站产量，非净化水脚注说明用于花园和道路灌溉；产量不等于实际消费。全国净化水总数2021/22为11167、2020/21为10992百万立方米，另一本CAPMAS水和污水年报同年分别11167.1、10991.8，接近整数取整但报告未说明差异原因，不自行认定。总量与省份重叠；Cairo/Giza非CBD。'}
