"""医保局 2023—2025 年医保结算住院疾病 Top10 原表。"""
import release_runtime
from pathlib import Path
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/8/7/art_257_21685.html'
TABLE_URL = 'https://www.nhsa.gov.cn/picture/0/00153c5140554efe93fdfc53bd593f8b.png'
IMAGE_PATH = Path(__file__).with_name('医保结算住院疾病TOP10原表.png')
ROWS = (('脑梗死', '45044094', '8441.23'), ('肺感染', '21424923', '6134.96'), ('冠状动脉粥样硬化性心脏病', '20602901', '10326.02'), ('支气管肺炎', '19169128', '2856.17'), ('2型糖尿病', '18697261', '6748.39'), ('腰椎间盘突出', '17581951', '5919.05'), ('高血压', '14905463', '7119.26'), ('急性支气管炎', '14296197', '2132.32'), ('腹痛', '13539268', '7007.16'), ('急性上呼吸道感染', '6295799', '2162.38'))

def nhsa_disease_top10_2023_2025(keyword=''):
    """查询原表按 2023—2025 年标注的出院人次和次均费用。"""
    keyword = keyword.strip()
    return [{'rank': i, 'diagnosis': name, 'discharge_count': count, 'discharge_count_unit': '人次', 'mean_cost': cost, 'mean_cost_unit': '元', 'period': '2023—2025', 'source_url': SOURCE_URL, 'source_image_url': TABLE_URL, 'local_image': str(IMAGE_PATH), 'extraction': '人工逐行核对原图'} for i, (name, count, cost) in enumerate(ROWS, 1) if not keyword or keyword in name]
