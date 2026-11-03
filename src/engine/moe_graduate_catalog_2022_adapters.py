"""读取研究生教育学科专业目录（2022 年）官方原版 PDF。"""
import release_runtime
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('研究生教育学科专业目录2022.pdf')
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A22/moe_833/202209/W020220914572994461110.pdf'

def search_graduate_catalog_2022(keyword=''):
    """按代码或名称子串查询历史目录；空关键词返回全部条目。"""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    rows, category = ([], None)
    for pageno, page in enumerate(PdfReader(str(PDF_PATH)).pages[2:], 3):
        for line in (page.extract_text() or '').splitlines():
            line = line.strip()
            if not line or re.fullmatch('—\\s*\\d+\\s*—', line):
                continue
            match = re.match('^(\\d{2}|\\d{4})\\s+(.+)$', line)
            if match:
                code, value = match.groups()
                if len(code) == 2:
                    category = {'code': code, 'name': value}
                    kind = '学科门类'
                else:
                    kind = '专业学位类别' if int(code[2]) >= 5 else '一级学科'
                rows.append({'code': code, 'text': value, 'kind': kind, 'category_code': category['code'] if category else None, 'category_name': category['name'] if category else None, 'pages': [pageno]})
            elif rows:
                rows[-1]['text'] += line
                if pageno not in rows[-1]['pages']:
                    rows[-1]['pages'].append(pageno)
            else:
                raise ValueError('PDF 解析失败：发现不属于任何条目的文本')
    if len([r for r in rows if r['kind'] == '学科门类']) != 14:
        raise ValueError('PDF 解析失败：学科门类数量异常')
    for row in rows:
        row['text'] = re.sub('\\s+', '', row['text'])
        row['name'] = re.split('[（*]', row['text'], 1)[0]
        row['master_only'] = row['kind'] == '专业学位类别' and '*' in row['text']
        row['source_url'] = SOURCE_URL
        row['published_year'] = 2022
    keyword = keyword.strip()
    return [r for r in rows if not keyword or keyword in r['code'] or keyword in r['text']]
