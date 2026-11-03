"""Guard Crossref works metadata before shaping catalogue results."""
import release_runtime

def validate_crossref_page(message, rows):
    if not isinstance(message, dict) or not isinstance(message.get('items'), list) or len(message['items']) > rows:
        raise RuntimeError('Crossref 结果列表或数量异常')
    total = message.get('total-results')
    if isinstance(total, bool) or not isinstance(total, int) or total < 0 or (len(message['items']) > total):
        raise RuntimeError('Crossref 结果总数异常')
    for item in message['items']:
        if not isinstance(item, dict):
            raise RuntimeError('Crossref 题录格式异常')
        title = item.get('title') or []
        container = item.get('container-title') or []
        authors = item.get('author', [])
        if not isinstance(title, list) or any((not isinstance(x, str) for x in title)) or (not isinstance(container, list)) or any((not isinstance(x, str) for x in container)) or (not isinstance(authors, list)) or any((not isinstance(x, dict) for x in authors)):
            raise RuntimeError('Crossref 标题或作者格式异常')
