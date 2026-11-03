"""Fixed official CAPMAS 2022/23 water bulletin, source table verification."""
import release_runtime
import hashlib, os, subprocess, tempfile
from pathlib import Path
import fitz
URL = 'https://metadata.capmas.gov.eg/en/index.php/catalog/675/download/2008'
SHA256 = 'd364ce02dca42047cc3908bb539573a1d2fd0138012f6a731b546bb0d48b5b63'

def _hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def download(destination):
    path = release_runtime.expandpath(Path(destination))
    if os.path.lexists(path):
        raise FileExistsError('Destination already exists')
    if not path.parent.is_dir():
        raise ValueError('Destination directory does not exist')
    fd, tmp = tempfile.mkstemp(prefix='.capmas-water-', suffix='.pdf', dir=path.parent)
    os.close(fd)
    try:
        try:
            release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '90', '--max-filesize', '15000000', '-o', tmp, URL], check=True, capture_output=True, timeout=95)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError('Official download failed: ' + type(exc).__name__) from None
        if _hash(tmp) != SHA256:
            raise RuntimeError('Official PDF changed; verify before use')
        with fitz.open(tmp) as p:
            if len(p) != 60:
                raise RuntimeError('Unexpected page count')
        os.link(tmp, path)
        return {'path': str(path.absolute()), 'bytes': path.stat().st_size, 'sha256': SHA256, 'source_url': URL, 'pages': 60}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')

        def rows(i, ys, b):
            return [[p[i].get_textbox(fitz.Rect(a, y - 1, c, y + 11)).strip() for a, c in b] for y in ys]
        a = rows(18, [198.2, 342.2], [(438, 465), (377, 418), (321, 357), (260, 285), (187, 215)])
        b = rows(19, [245.2], [(78, 132), (475, 510), (414, 460), (340, 384), (266, 315), (218, 251), (160, 195)])
        c = rows(21, [226.7, 244.4, 439.9], [(82, 145), (453, 495), (398, 437), (330, 385), (272, 310), (193, 225)])
        chart = p[18].get_text()
    if a != [['2792', '11287.5', '8892.1', '100', '100'], ['36', '2074', '2074', '18.4', '23.3']] or b != [['2022/2023', '2792', '11287.5', '8892.1', '105914499', '106.6', '84']] or c != [['Total', '11287.5', '8892.1', '105914499', '106.6', '84.0'], ['Cairo', '1784.9', '1411.5', '10299821', '173.3', '137.0'], ['Giza', '1449.7', '1194.6', '9578680', '151.3', '124.7']] or ('0.0' not in chart):
        raise RuntimeError('Water bulletin differs from visually reviewed source')
    ka = ['stations', 'produced_million_m3', 'consumed_million_m3', 'produced_share_percent', 'consumed_share_percent']
    kb = ['period', 'stations', 'produced_million_m3', 'consumed_million_m3', 'population_estimate', 'produced_m3_per_capita', 'consumed_m3_per_capita']
    kc = ['area', 'produced_million_m3', 'consumed_million_m3', 'population_estimate', 'produced_m3_per_capita', 'consumed_m3_per_capita']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'period': '2022/2023', 'entity_table_physical_page': 19, 'per_capita_table_physical_page': 20, 'governorates_table_physical_page': 22, 'entities': [{'entity': 'Total', **dict(zip(ka, a[0]))}, {'entity': 'New Urban Communities Authority', **dict(zip(ka, a[1]))}], 'national_per_capita': dict(zip(kb, b[0])), 'governorate_rows': [dict(zip(kc, r)) for r in c], 'note': '原表单位为百万立方米和人均立方米，覆盖控股公司、苏伊士运河管理局及新城市社区管理局设施，并非 CBD 单独数据。NUCA 同表自产与消费均2074；另一表脚注称生产量等于售出量，不能推论实际无损耗。同页生产占比表为18.4%，饼图对应标0.0%，二者不一致，保留原表及差异；省级表脚注称总消费量与各省消费量之和无关，不能强行汇总。2022/23 使用人口估计105914499，恰与另一CAPMAS原刊2024-01-01全国人口数一致，仅为数值对照，不推断本表时间标注。人均总供水或消费不等于居民生活用水或水质安全。'}

def new_cities_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(88, 150), (177, 208), (237, 254), (280, 315), (330, 346), (373, 408), (430, 448), (478, 510), (528, 544), (564, 597), (610, 626)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[34]
        rows = [[page.get_textbox(fitz.Rect(a, y - 1, b, y + 10)).strip() for a, b in bounds] for y in (245.5, 257.1)]
        raw = page.get_text()
    expected = [['Total', '2074', '36', '2074', '36', '129.2', '8', '31.8', '3', '1913', '25'], ['New Cairo', '182.5', '1', '182.5', '1', '0', '0', '0', '0', '182.5', '1']]
    if rows != expected or 'Quantity of water produced = Amount of water sold' not in raw:
        raise RuntimeError('Water city table differs from visually reviewed source')
    keys = ['city_as_printed', 'governorate_total_water_million_m3', 'governorate_station_count', 'city_total_water_million_m3', 'city_station_count', 'desalination_water_million_m3', 'desalination_station_count', 'wells_desalination_water_million_m3', 'wells_desalination_station_count', 'surface_water_million_m3', 'surface_station_count']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 35, 'printed_page': 28, 'period': '2022/2023', 'quantity_unit': 'million m3', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表仅指新城市社区管理局所属设施，选取总计与 New Cairo 原行；New Cairo 是新开罗，不是新行政首都 CBD。表格未单列新行政首都，不能推断其无供水或无设施。原脚注称生产量等于售出量，不能当作实际零损耗证明。总计与城市、省份分项重叠，不能重复相加；分省合并单元格不能套给其他城市。'}

def sewage_cities_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(112, 175), (250, 283), (342, 362), (383, 422), (437, 466), (487, 510), (532, 552), (572, 593), (609, 627)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[43]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.5, b, y + 9)).strip() for a, b in bounds] for y in (247.1, 271.8)]
        gov = page.get_textbox(fitz.Rect(298, 275, 316, 287)).strip()
        raw = page.get_text()
    expected = [['Total', '731.5', '36', '523.2', '186.4', '21.9', '22', '13', '1'], ['New Cairo', '120.4', '2', '120.4', '0', '0', '2', '0', '0']]
    if rows != expected or gov != '36' or 'Amount of Treated sewage = Amount of Collective sewage' not in raw:
        raise RuntimeError('Sewage city table differs from visually reviewed source')
    keys = ['city_as_printed', 'city_treated_million_m3', 'city_stations', 'triple_treated_million_m3', 'binary_treated_million_m3', 'primary_treated_million_m3', 'triple_stations', 'binary_stations', 'primary_stations']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 44, 'printed_page': 37, 'period': '2022/2023', 'quantity_unit': 'million m3', 'rows': [dict(zip(keys, r)) for r in rows], 'cairo_governorate_station_count_as_printed': gov, 'note': '只提取 NUCA 污水表总计及新开罗行；New Cairo 非新行政首都，未单列后者不代表无设施。原表 Cairo 省合并站数印为36，与下列四个城市站数1、2、1、2之和6不一致，原因未核，不能自行修正。脚注称处理量等于收集量，不证明该范围以外全部污水得到安全处理；各处理级别与总数重叠，不能重复相加。全国及CBD不能由该机构子集代表。'}

def water_samples_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(63, 100), (450, 490), (399, 430), (343, 384), (290, 320), (238, 261), (189, 212)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[28]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.5, b, y + 10)).strip() for a, b in bounds] for y in (252.6, 272.8, 448.4)]
    expected = [['Total', '2798067', '17883', '2397408', '36290', '0.64', '1.51'], ['Cairo', '267075', '0', '238748', '0', '0', '0'], ['Giza', '40920', '709', '196617', '3417', '1.73', '1.74']]
    if rows != expected:
        raise RuntimeError('Water sample table differs from visually reviewed source')
    keys = ['area_as_printed', 'production_samples', 'production_nonmatching_samples', 'distribution_samples', 'distribution_nonmatching_samples', 'production_nonmatching_percent', 'distribution_nonmatching_percent']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 29, 'printed_page': 22, 'period': '2022/2023', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表标题写 matching percentage，但列标题明确为 non-matching，输出按列标题保留不合格样本数及百分比。仅控股公司旗下水公司站点和分销网络已送检样本，非全部水源、家庭用户或 NUCA/CBD；Cairo 表中零不合格仅限所列样本，不能证明全部用水安全或代表当前水质。全国总计与省行重叠；抽样方法、采样点和检测指标须查原刊。'}

def sewage_national_series(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(188, 230), (264, 285), (329, 360), (384, 420)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[45]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.7, b, y + 10)).strip() for a, b in bounds] for y in (347, 367.4, 390.1)]
    expected = [['2022/2023', '89.2', '6063.8', '5407.3'], ['2021/2022', '86.2', '6069', '5234.1'], ['2020/2021', '85.8', '6102', '5233.6']]
    if rows != expected:
        raise RuntimeError('National sewage series differs from visually reviewed source')
    keys = ['period_as_printed', 'treated_share_percent', 'collective_sewage_million_m3', 'treated_sewage_million_m3']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 46, 'printed_page': 39, 'quantity_unit': 'million m3', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原刊将表放在 SDG 6.3.1 安全处理标题下，但实际表格分母写 collective sewage（收集的污水），不证明其覆盖全部产生的污水或可直接与其他定义的SDG指标比较；处理量、收集量和百分比保留原始数。全国历史资料非新行政首都或 CBD 的处理率，不能将处理量与总收集量相加。'}

def water_network_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(74, 115), (471, 506), (426, 460), (382, 416), (338, 360), (284, 316), (231, 270), (170, 210)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[26]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (225.5, 241.7, 457.5)]
        raw = page.get_text()
    expected = [['Total', '9129.4', '6746.6', '2382.8', '26.1', '156010', '18080948', '15273.2'], ['Cairo', '1602.4', '1229.0', '373.4', '23.3', '8387', '1625985', '44516.4'], ['Giza', '996.3', '741.2', '255.1', '25.6', '7987', '1080260', '31931.6']]
    if rows != expected or 'not related to the sum of the amounts of loss' not in raw:
        raise RuntimeError('Water network table differs from visually reviewed source')
    keys = ['area_as_printed', 'produced_million_m3', 'consumed_million_m3', 'loss_non_refundable_million_m3', 'loss_percent', 'network_length_as_printed', 'subscriptions_as_printed', 'loss_m3_per_km_as_printed']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 27, 'printed_page': 20, 'period': '2022/2023', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '仅控股公司下属水公司，非全部三类机构或 CBD；损失原文又称 non-refundable water（未计费水），不能将全部视作物理漏水。数量为百万立方米、比率为百分数，末列原文 m3/km；网络长度列本页未明确单位，原样保留。脚注称全国总消费和总损失依据控股公司核算，不等于各省值简单加总。Cairo/Giza 指该公司的省级数据，并非全省所有供水系统。'}

def utility_revenue_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(86, 125), (432, 470), (380, 414), (319, 350), (258, 290), (195, 232)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[51]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.5, b, y + 11)).strip() for a, b in bounds] for y in (199.3, 221.6, 443.4)]
    expected = [['Total', '28388.7', '876.7', '1570.6', '2347.5', '33183.5'], ['Cairo', '6639.6', '16.0', '360.5', '481.0', '7497.1'], ['Giza', '2973.2', '6.4', '115.4', '338.8', '3433.8']]
    if rows != expected:
        raise RuntimeError('Utility revenue table differs from visually reviewed source')
    keys = ['area_as_printed', 'revenue_current_activity', 'grants_subsidies', 'income_investments_benefits', 'other_income_profits', 'total_revenue']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 52, 'printed_page': 45, 'period': '2022/2023', 'unit_as_printed': 'Mil. L.E.', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '原表为控股公司水及污水公司的收入项目，金额百万埃镑；总收入包含补贴、投资收益及其他收入，非水费收入、净利润、现金流或 CBD 运营商收入。总计和分项重叠；所选省级公司仅对应所属机构而非该省所有运营商。'}

def utility_costs_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    bounds = [(101, 137), (420, 455), (356, 382), (297, 325), (245, 278), (200, 230)]
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        page = p[55]
        rows = [[page.get_textbox(fitz.Rect(a, y - 0.5, b, y + 10)).strip() for a, b in bounds] for y in (244.5, 268.3, 491.6)]
    expected = [['Total', '7970', '862', '8832', '35704', '44536'], ['Cairo', '1674', '241', '1915', '6710', '8625'], ['Giza', '929', '139', '1068', '3567', '4635']]
    if rows != expected:
        raise RuntimeError('Utility costs table differs from visually reviewed source')
    keys = ['area_as_printed', 'commodity_requirements', 'service_requirements', 'commodity_service_total', 'expenses_and_costs', 'total']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'physical_page': 56, 'printed_page': 49, 'period': '2022/2023', 'unit_as_printed': 'Mil. L.E.', 'rows': [dict(zip(keys, r)) for r in rows], 'note': '控股公司下属水污公司原表，保留商品和服务需求、费用及成本，总计与子项重叠。其 44536 百万埃镑总额与同刊收入总计33183.5口径关系未核，不应简单相减认定净亏损；不是现金支出或 CBD 运营成本，省份也非全部运营商。'}

def utility_staff_selected(path):
    path = release_runtime.expandpath(Path(path))
    if _hash(path) != SHA256:
        raise ValueError('File does not match verified official snapshot')
    specs = [(48, [193.5, 207.4, 356.6], [(35, 90), (150, 190), (215, 245), (270, 299), (332, 365), (405, 438), (480, 515), (553, 583), (617, 642)]), (49, [274.7, 295.7, 497.2], [(100, 135), (425, 465), (360, 395), (306, 340), (265, 292), (205, 235)])]
    expected = [[['Total', '211532', '63955', '7837', '51759', '21445', '48721', '16691', '1124'], ['Cairo', '27684', '7699', '1479', '8738', '3311', '4483', '1892', '82'], ['Giza', '15604', '4427', '752', '4742', '1960', '2203', '1432', '88']], [['Total', '11184.5', '1634.5', '12819', '194', '13013'], ['Cairo', '2006.5', '258.1', '2264.6', '63.8', '2328.4'], ['Giza', '994.6', '134.5', '1129.1', '53.2', '1182.3']]]
    data = []
    with fitz.open(path) as p:
        if len(p) != 60:
            raise RuntimeError('Unexpected page count')
        for idx, (i, ys, bounds) in enumerate(specs):
            rows = [[p[i].get_textbox(fitz.Rect(a, y - 0.6, b, y + 11)).strip() for a, b in bounds] for y in ys]
            if rows != expected[idx]:
                raise RuntimeError('Utility staff table differs from visually reviewed source')
            data.append(rows)
    staffkeys = ['area_as_printed', 'employees', 'temporary_workers', 'other_jobs', 'operators_and_technical_services', 'administrators_and_clerks', 'production_supervisors_and_observers', 'specialists_and_technicians', 'managers']
    paykeys = ['area_as_printed', 'cash_wages', 'social_insurance', 'cash_wages_and_insurance', 'in_kind_benefits', 'total_wages_insurance_and_benefits']
    return {'source': 'CAPMAS Annual Bulletin of Pure Water and Sanitation Statistics 2022/2023', 'source_url': URL, 'sha256': SHA256, 'staff_physical_page': 49, 'staff_printed_page': 42, 'pay_physical_page': 50, 'pay_printed_page': 43, 'period': '2022/2023', 'staff_unit': 'persons', 'pay_unit_as_printed': 'Mil. L.E.', 'staff_rows': [dict(zip(staffkeys, r)) for r in data[0]], 'pay_rows': [dict(zip(paykeys, r)) for r in data[1]], 'note': '仅控股公司下属水污公司，工作人员为原表人数，工资和社会保险、实物福利为年度总额，单位百万埃镑。职位、临时工与总人数按原表列出；不详人员时间覆盖和报酬包含范围，不能直接相除得平均工资。省级数据不是所有公共服务部门或 CBD 员工；合计与子项重叠。'}
