"""浙大馆藏 JAMA 期刊介绍中的历史名单快照。"""
import release_runtime
import json
_ROWS = [('JAMA', 'https://jamanetwork.com/journals/jama'), ('JAMA Cardiology', 'https://jamanetwork.com/journals/jamacardiology'), ('JAMA Dermatology', 'https://jamanetwork.com/journals/jamadermatology'), ('JAMA Facial Plastic Surgery', 'http://archfaci.jamanetwork.com/journal.aspx'), ('JAMA Internal Medicine', 'https://jamanetwork.com/journals/jamainternalmedicine'), ('JAMA Neurology', 'https://jamanetwork.com/journals/jamaneurology'), ('JAMA Oncology', 'https://jamanetwork.com/journals/jamaoncology'), ('JAMA Ophthalmology', 'https://jamanetwork.com/journals/jamaophthalmology'), ('JAMA Otolaryngology-Head & Neck Surgery', 'https://jamanetwork.com/journals/jamaotolaryngology'), ('JAMA Pediatrics', 'https://jamanetwork.com/journals/jamapediatrics'), ('JAMA Psychiatry', 'https://jamanetwork.com/journals/jamapsychiatry'), ('JAMA Surgery', 'https://jamanetwork.com/journals/jamasurgery')]

def journals(keyword=''):
    if not isinstance(keyword, str):
        raise TypeError('keyword 必须为字符串')
    found = [{'title': t, 'url': u} for t, u in _ROWS if keyword.casefold() in t.casefold()]
    return {'source_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1006', 'snapshot_date': '2026-10-29', 'keyword': keyword, 'total_listed': len(_ROWS), 'matched': len(found), 'items': found, 'scope': '馆方页面列举的历史12刊，原链接未经逐条验证，不代表现行全库、订购或单篇全文权限。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    print(json.dumps(journals(p.parse_args().keyword), ensure_ascii=False, indent=2))
