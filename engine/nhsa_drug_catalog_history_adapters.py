"""国家医保局 2000—2025 年医保药品目录历史统计原表。"""
import release_runtime
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/8/5/art_257_21672.html'
PDF_URL = 'https://www.nhsa.gov.cn/module/download/downfile.jsp?classid=0&filename=49e01eeefa02436aa748c9f174fdbb7c.pdf'
YEARS = (2000, 2004, 2009, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
ROWS = {'药品数量（西药和中成药编号）': ('1535', '1901', '2196', '2571', '2588', '2709', '2800', '2860', '2967', '3088', '3159', '3253'), '西药': ('913', '1031', '1164', '1328', '1345', '1370', '1426', '1486', '1586', '1698', '1765', '1857'), '中成药': ('622', '870', '1032', '1243', '1243', '1339', '1374', '1374', '1381', '1390', '1394', '1396'), '其中：协议期内谈判品种': ('/', '/', '/', '36', '53', '114', '221', '275', '363', '430', '427', '472'), '中药饮片': ('按排除法管理', '按排除法管理', '按排除法管理', '按排除法管理', '按排除法管理', '892', '892', '892', '892', '892', '892', '892'), '新增谈判准入药品': ('/', '/', '/', '36', '17', '70', '96', '67', '108', '121', '89', '112'), '抗肿瘤药物（西药）': ('54', '72', '87', '85', '91', '106', '118', '131', '144', '164', '186', '219'), '罕见病治疗药物': ('/', '/', '/', '/', '39', '48', '61', '69', '83', '98', '111', '121'), '儿童用药': ('/', '/', '/', '580余种', '新增1', '新增76', '新增34', '新增16', '新增28', '新增33', '新增17', '新增25')}

def drug_catalog_history(year=None, keyword=''):
    """返回版本年份和原表文本；原版未列示标记与增量表述保持原样。"""
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or year not in YEARS):
        raise ValueError('year 必须是原表中的目录版本年份')
    keyword = keyword.strip()
    return [{'version_year': y, 'indicator': name, 'original_value': value, 'source_url': SOURCE_URL, 'pdf_url': PDF_URL, 'pdf_page': 1, 'extraction': '人工逐格核对原 PDF 转录'} for name, values in ROWS.items() if not keyword or keyword in name for y, value in zip(YEARS, values) if year is None or year == y]
