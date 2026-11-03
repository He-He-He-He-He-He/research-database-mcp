"""浙大古籍特藏原始全类型分页检查。"""
import release_runtime

def _validate_page(data, page):
    total = data.get('total_count') if isinstance(data, dict) else None
    rows = data.get('data') if isinstance(data, dict) else None
    if isinstance(total, bool) or not isinstance(total, int) or total < 0 or (not isinstance(rows, list)) or (len(rows) > 20) or (len(rows) > max(0, total - (page - 1) * 20)) or any((not isinstance(row, dict) for row in rows)):
        raise RuntimeError('原始结果总数与分页记录异常')
    if data.get('page_index') != (page - 1) * 20 or data.get('page_size') != 20:
        raise RuntimeError('原站回显页码或每页数量不一致')
