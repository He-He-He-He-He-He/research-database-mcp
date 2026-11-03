"""Bounded batch orchestration. Every item goes through the normal access gate."""
import time,threading
from concurrent.futures import ThreadPoolExecutor
import release_runtime as rt
from research_cli import query
from result_store import present

def batch(queries,max_workers=3,output='auto',export_format='json',deadline_seconds=110):
    if not isinstance(queries,list) or not 1<=len(queries)<=12:raise ValueError('每批须1至12个查询')
    if type(max_workers) is not int or not 1<=max_workers<=4:raise ValueError('max_workers须1至4')
    if type(deadline_seconds) not in (int,float) or not 5<=deadline_seconds<=120:raise ValueError('批次时间预算须5至120秒')
    if output not in ('auto','full','compact','file') or export_format not in ('json','csv'):raise ValueError('输出选项无效')
    for item in queries:
        if not isinstance(item,dict) or set(item)-{'command','args','id'} or not isinstance(item.get('command'),str) or not isinstance(item.get('args'),list):raise ValueError('每项须包含command和args，可选id')
        if 'id' in item and (not isinstance(item['id'],str) or len(item['id'])>64):raise ValueError('id须为最多64字符的字符串')
    end=time.monotonic()+deadline_seconds;state=rt.state_root()
    locks={item['command'].split('-')[0]:threading.Lock() for item in queries}
    def worker(pair):
        index,item=pair;lock=locks[item['command'].split('-')[0]]
        left=end-time.monotonic()
        if left<=0 or not lock.acquire(timeout=max(0,left)):
            value={'ok':False,'skipped':True,'error':'batch_deadline','message':'批次时间预算已用完；未发起本项请求。'}
        else:
            try:
                left=end-time.monotonic()
                if left<=0:value={'ok':False,'skipped':True,'error':'batch_deadline'}
                else:
                    with rt.using_state(state):value=query(item['command'],item['args'],timeout=min(90,max(.1,left-.1)),output='full')
            except (ValueError,TypeError) as exc:value={'ok':False,'error':'invalid_arguments','message':str(exc)}
            except Exception:value={'ok':False,'error':'local_execution_error','message':'本项执行失败，其他项继续；请单独查询定位。'}
            finally:lock.release()
        return {'id':item.get('id',str(index+1)),'command':item['command'],**value}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:items=list(pool.map(worker,enumerate(queries)))
    passed=sum(bool(item.get('ok')) for item in items)
    # A batch artifact contains each item verbatim; failures are never dropped.
    result={'ok':passed==len(items),'partial':0<passed<len(items),'passed':passed,'failed':len(items)-passed,'total':len(items),'result':items,'verification':'每项分别执行和记录；并发不保证固定提速，来源限流和缺失值仍需核对。'}
    result['data_summary']={'requests_ok':passed,'nonempty_results':sum(x.get('has_records') is True for x in items),'content_results':sum(x.get('has_content') is True for x in items),'catalog_results':sum(x.get('content_level')=='catalog' for x in items),'bibliographic_results':sum(x.get('content_level')=='bibliographic' for x in items),'snippet_results':sum(x.get('content_level')=='snippet' for x in items),'empty_results':sum(x.get('result_status')=='empty_result' for x in items),'numeric_results':sum(x.get('data_verified') is True for x in items),'missing_observations':sum(x.get('result_status')=='missing_observations' for x in items),'unverified_results':sum(x.get('result_status') in ('unclassified','observations_unverified') for x in items)}
    result['verification']='passed/requests_ok只表示请求完成，不表示每项取得记录或数值；请检查data_summary及每项result_status、record_count、numeric_observation_count。'
    return present(result,output,export_format)
