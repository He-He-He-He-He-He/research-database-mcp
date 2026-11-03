"""中国视听大数据收视日历公开目录与剧目收视记录。"""
import release_runtime
from cvb_rankings_adapters import _get, _page_params

def calendars(page=1, size=20):
    """官网已发布的收视日历图片目录；返回原始图片路径。"""
    page, size = _page_params(page, size)
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量须为 1—100')
    return _get('calendar/list', {'pageNum': page, 'pageSize': size, 'status': 1})

def program(name, channel='', page=1, size=10):
    """按剧名和可选频道分页查收视数据，返回官网原始记录。"""
    page, size = _page_params(page, size)
    if not isinstance(name, str) or not name.strip() or (not isinstance(channel, str)) or (page < 1) or (not 1 <= size <= 100):
        raise ValueError('需剧名、正页码和 1—100 每页数量')
    params = {'name': name, 'pageNum': page, 'pageSize': size}
    if channel:
        params['channel'] = channel
    return _get('viewing_calendar/detailList', params)
