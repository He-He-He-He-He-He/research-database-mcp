"""Validate the count of a parsed ZJU Wenku catalogue page."""
import release_runtime

def validate_page_count(total, pages, page, items, page_size):
    if total < 0 or pages < 0 or page < 1 or (page_size < 1) or (total > 0 and (pages != (total + page_size - 1) // page_size or page > pages)) or (len(items) != min(page_size, max(0, total - (page - 1) * page_size))):
        raise RuntimeError('目录页面总数、页数与已解析记录不一致')
