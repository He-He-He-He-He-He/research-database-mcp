"""智慧古籍人物/专题目录返回页元数据校验。"""
import release_runtime

def validate_page(result, page, page_size):
    if not isinstance(result, dict) or not isinstance(result.get('list'), list):
        raise ValueError('unexpected catalogue response')
    total = result.get('total')
    pages = result.get('pages')
    rows = result['list']
    if type(total) is not int or total < 0 or type(pages) is not int or (pages != (total + page_size - 1) // page_size) or (result.get('pageNum') != page) or (result.get('pageSize') != page_size) or (len(rows) != min(page_size, max(0, total - (page - 1) * page_size))) or any((not isinstance(x, dict) for x in rows)):
        raise ValueError('catalogue pagination or records inconsistent')
