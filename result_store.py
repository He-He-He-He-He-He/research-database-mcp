"""Private local exports and bounded previews. Exported research is never packaged."""
import csv,hashlib,io,json,os,re,tempfile,uuid
from pathlib import Path
import release_runtime as rt

INLINE_LIMIT=24000
MAX_BYTES=20000000

def rows_at(value):
    if isinstance(value,list):
        if len(value)==2 and isinstance(value[0],dict) and isinstance(value[1],list):return value[1],'/1'
        return value,''
    if isinstance(value,dict):
        for key in ('items','rows','data','value','results','records'):
            if isinstance(value.get(key),list):return value[key],'/'+key
        for key in ('message','resultList'):
            child=value.get(key)
            if isinstance(child,dict):
                for name in ('items','result'):
                    if isinstance(child.get(name),list):return child[name],'/'+key+'/'+name
    return None,None

def preview(value,items=3,depth=0):
    if depth>5:return {'_preview_omitted':True}
    if isinstance(value,dict):
        out={str(k):preview(v,items,depth+1) for k,v in list(value.items())[:20]}
        if len(value)>20:out['_preview_omitted_keys']=len(value)-20
        return out
    if isinstance(value,list):
        return {'items':[preview(x,items,depth+1) for x in value[:items]],'stored_count':len(value),'preview_only':len(value)>items}
    if isinstance(value,str) and len(value)>600:return value[:600]+'… [预览截断，完整内容在结果文件]'
    return value

def _directory(result_id):
    if not isinstance(result_id,str) or not re.fullmatch('[0-9a-f]{32}',result_id):raise ValueError('结果编号无效')
    base=rt.state_root()/'results'
    path=base/result_id
    if base.is_symlink() or path.is_symlink():raise ValueError('结果目录不能是符号链接')
    return path

def _csv(rows):
    normalized=[r if isinstance(r,dict) else {'value':r} for r in rows]
    columns=list(dict.fromkeys(k for row in normalized for k in row))
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=columns,lineterminator='\n');writer.writeheader()
    for row in normalized:
        data={}
        for key,value in row.items():
            if isinstance(value,(dict,list)):value=json.dumps(value,ensure_ascii=False)
            # Spreadsheet formula strings are escaped; raw JSON remains exact.
            if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):value="'"+value
            data[key]=value
        writer.writerow(data)
    return '\ufeff'+out.getvalue()

def save(result,export_format='json'):
    raw=json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8')
    if len(raw)>MAX_BYTES:raise ValueError('结果过大，请缩小查询后导出')
    result_id=uuid.uuid4().hex;folder=_directory(result_id)
    folder.mkdir(parents=True,mode=0o700)
    paths={'json':folder/'result.json'}
    try:
        paths['json'].write_bytes(raw);os.chmod(paths['json'],0o600)
        rows,pointer=rows_at(result.get('result'))
        if export_format=='csv':
            if rows is None:rows=[result.get('result',result)]
            paths['csv']=folder/'result.csv';paths['csv'].write_text(_csv(rows),encoding='utf-8',newline='');os.chmod(paths['csv'],0o600)
        artifacts=[]
        for kind,path in paths.items():
            artifacts.append({'format':kind,'path':str(path),'uri':'research://result/'+result_id+'/'+kind,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        return {'result_id':result_id,'artifacts':artifacts,'stored_rows':len(rows) if rows is not None else None,'rows_pointer':'/result'+pointer if pointer is not None else None}
    except Exception:
        for path in paths.values():
            if path.exists():path.unlink()
        folder.rmdir();raise

def present(result,output='auto',export_format='json'):
    size=len(json.dumps(result,ensure_ascii=False))
    if not result.get('ok') and 'result' not in result and 'items' not in result:return result
    if output=='auto' and size<=INLINE_LIMIT and export_format=='json':return result
    if output=='full' and size<=1500000 and export_format=='json':return result
    exported=save(result,export_format)
    if output=='full' and size<=1500000:return {**result,**exported}
    out={k:result[k] for k in ('ok','command','partial','source','result_kind','warnings','verification','passed','failed','total') if k in result}
    out.update(exported,inline_complete=False,output='file' if output=='file' else 'compact',notice='这是预览或文件引用。完整JSON保留原始值、来源、口径、分页与失败信息；存储行数不代表源站全部记录。文件在接收者自己的包外状态目录，需自行保管和清理。')
    if output!='file':
        out['preview']=preview(result.get('result',result))
        if len(json.dumps(out,ensure_ascii=False))>INLINE_LIMIT:out['preview']={'_preview_omitted':True,'hint':'使用research_result按指针和分页读取'}
    return out

def read(result_id,kind='json'):
    if kind not in ('json','csv'):raise ValueError('结果格式无效')
    path=_directory(result_id)/('result.'+kind)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_BYTES:raise ValueError('结果文件缺失、过大或不安全')
    return path.read_text(encoding='utf-8')

def fetch(result_id,pointer=None,offset=0,limit=20):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=200:raise ValueError('offset须非负，limit须1至200')
    result=json.loads(read(result_id));node=result
    if pointer is None:
        rows,path=rows_at(result.get('result'))
        if path is not None:pointer='/result'+path
        else:pointer=''
    if not isinstance(pointer,str) or len(pointer)>500 or (pointer and not pointer.startswith('/')):raise ValueError('pointer须为JSON指针')
    try:
        for part in pointer.split('/')[1:] if pointer else []:
            key=part.replace('~1','/').replace('~0','~')
            if isinstance(node,list):
                if not re.fullmatch('0|[1-9][0-9]*',key):raise ValueError('列表索引无效')
                node=node[int(key)]
            else:node=node[key]
    except (KeyError,IndexError,TypeError):raise ValueError('结果中没有该JSON指针') from None
    if isinstance(node,list):
        selected=[]
        for row in node[offset:offset+limit]:
            if len(json.dumps(selected+[row],ensure_ascii=False))>INLINE_LIMIT:
                if not selected:return {'ok':True,'result_id':result_id,'pointer':pointer,'offset':offset,'total_rows_stored':len(node),'items':[],'next_offset':offset,'row_too_large':True,'hint':'该行超出回传预算，请用pointer选择行内字段，或读取本机完整文件。'}
                break
            selected.append(row)
        end=offset+len(selected)
        return {'ok':True,'result_id':result_id,'pointer':pointer,'offset':offset,'total_rows_stored':len(node),'items':selected,'next_offset':end if end<len(node) else None}
    value=node if len(json.dumps(node,ensure_ascii=False))<=INLINE_LIMIT else preview(node)
    if len(json.dumps(value,ensure_ascii=False))>INLINE_LIMIT:value={'_preview_omitted':True,'hint':'内容超出回传预算，请用pointer进一步选择字段，或读取完整本机文件'}
    return {'ok':True,'result_id':result_id,'pointer':pointer,'value':value,'preview_only':value is not node}
