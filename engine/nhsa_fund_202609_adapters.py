"""2026 年 1—9 月医保统筹基金主要指标：来源图片人工核对转录。"""
import release_runtime
from pathlib import Path
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/10/21/art_7_23187.html'
IMAGE_URL = 'https://www.nhsa.gov.cn/picture/0/s_9cf80d7b6514490f826ff62e83df737e.png'
IMAGE_PATH = Path(__file__).with_name('2026年1至9月医保基金主要指标原表.png')
ROWS = [('统筹基金收入', '基本医疗保险（含生育保险）', 0, '23028.33'), ('统筹基金收入', '职工基本医疗保险（含生育保险）', 1, '14473.64'), ('统筹基金收入', '城乡居民基本医疗保险', 1, '8554.69'), ('统筹基金支出', '基本医疗保险（含生育保险）', 0, '17515.19'), ('统筹基金支出', '职工基本医疗保险（含生育保险）', 1, '10044.28'), ('统筹基金支出', '其中：生育保险基金待遇支出', 2, '1010.10'), ('统筹基金支出', '城乡居民基本医疗保险', 1, '7470.91')]

def insurance_fund_202609(keyword=''):
    """查询人工核对的原表行；单位均为亿元。"""
    keyword = keyword.strip()
    return [{'period': '2026-01/2026-09', 'section': s, 'indicator': n, 'indent_level': depth, 'value': value, 'unit': '亿元', 'source_url': SOURCE_URL, 'source_image_url': IMAGE_URL, 'local_image': str(IMAGE_PATH), 'extraction': '人工核对原图转录'} for s, n, depth, value in ROWS if not keyword or keyword in s or keyword in n]
