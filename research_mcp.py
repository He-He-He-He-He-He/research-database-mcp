"""Portable newline-delimited stdio MCP server; stdout is protocol only."""
import sys
sys.dont_write_bytecode=True
import json
import sys
import re
import onboarding as setup
from research_cli import catalog, query
from distribution import VERSION
import access_policy as policy
import network_health

def tool(name,description,properties,required=()):
    return {'name':name,'description':description,'inputSchema':{'type':'object','properties':properties,'required':list(required),'additionalProperties':False},'annotations':{'readOnlyHint':name not in ('research_setup','research_verify'),'destructiveHint':False,'openWorldHint':True}}

STR={'type':'string'}
TOOLS=[
 tool('research_setup','三种模式：general一般（所有无需个人凭据/机构网络的命令）、zju浙大内网（再开放机构IP）、login登录（按需配置个人凭据）。旧partial/full兼容。可暂停恢复；network_status/reset查看或清除实际网络失败后的短暂跳过。不接收密码或密钥。',{'action':{'enum':['status','next','select','mark','skip','pause','resume','network_status','network_reset']},'mode':{'enum':[*policy.MODES,*policy.ALIASES]},'source':STR,'step':STR},['action']),
 tool('research_discover','按当前模式发现可尝试的查询命令；默认过滤模式不允许和近期网络失败命令。available_only=false可查看全部及阻碍原因。starter只是42条起步回归样例，不是一般模式的功能上限。静态分类不代表已验证可用。',{'keyword':STR,'limit':{'type':'integer','minimum':1,'maximum':40},'starter_only':{'type':'boolean'},'available_only':{'type':'boolean'},'kind':{'enum':['observations','catalog','metadata','bibliographic','text_search']}},['keyword']),
 tool('research_help','查看具体命令参数和需求，执行查询前调用。',{'command':STR},['command']),
 tool('research_query','先用research_help确认参数，再用字符串数组执行查询。数量参数可能是--size/--rows/--limit/--top，不能混用。不能传递凭据。',{'command':STR,'args':{'type':'array','items':STR,'maxItems':40}},['command','args']),
 tool('research_verify','真实执行指定来源的示例查询并保存验证结果；不能用帮助页或其他来源替代。一次成功不代表所有数据权限。',{'source':STR},['source']),
]

ALIASES={
 '统计':'wb worldbank cbs ons faostat bis census stat', '世界银行':'wb worldbank',
 '学术':'crossref arxiv pubmed epmc cinii wos scopus', '论文':'crossref arxiv pubmed epmc cinii wos scopus',
 '法律':'law case court npc spp', '政策':'policy ndrc gov', '人口':'population census demographic',
 '能源':'eia energy iea', '贸易':'wto trade asean', '气候':'climate nasa weather',
 '经济':'wb worldbank bis economic', '农业':'faostat fao agric', '荷兰':'cbs',
 '英国':'ons uk', '美国':'us usa census eia usgs', '中国':'china cn nbs npc',
 '化学':'cas chemistry', '免登录':'starter',
 '宏观':'nbs stats worldbank wb', 'gdp':'nbs 国内生产总值', '国内生产总值':'nbs gdp',
 '社零':'nbs 社会消费品零售总额', '社会消费品':'nbs 零售', 'pmi':'nbs 采购经理指数', 'cpi':'nbs 居民消费价格', 'ppi':'nbs 工业生产者价格',
}

def discover(keyword,limit=12,starter_only=False,kind=None,available_only=True):
    if not isinstance(keyword,str) or len(keyword)>200 or type(limit) is not int or not 1<=limit<=40 or type(starter_only) is not bool or type(available_only) is not bool:raise ValueError('发现参数无效')
    if kind not in (None,'observations','catalog','metadata','bibliographic','text_search'):raise ValueError('未知结果类型')
    words=keyword.casefold().split();expanded=set(words)
    for k,v in ALIASES.items():
        if k.casefold() in keyword.casefold():expanded.update(v.casefold().split())
    def score(x):
        text=' '.join([x['command'],*x.get('modules',[]),x.get('readiness',''),x.get('description',''),*x.get('topics',[])]).casefold()
        return sum(1 for w in expanded if w in text)+sum(3 for topic in x.get('topics',[]) if topic.casefold() in keyword.casefold())
    state=setup.rt.load_state();mode=state['mode'];rows=[];excluded={'mode':0,'network':0}
    # Load one cache snapshot, rather than reading the state file for each command.
    unavailable=network_health.status()['unavailable']
    for x in catalog():
        if (starter_only and not x.get('starter')) or (kind is not None and x.get('result_kind')!=kind) or (keyword.strip() and not score(x)):continue
        access=policy.describe(mode,x);network=unavailable.get('command:'+x['command'])
        if available_only and mode is not None and not access['allowed_in_mode']:excluded['mode']+=1;continue
        if available_only and network:excluded['network']+=1;continue
        rows.append({**x,'availability':{**access,'network':'recent_failure' if network else 'not_prechecked'}})
    rows.sort(key=lambda x:(-score(x),not x.get('starter'),x['command']))
    return {'matched':len(rows),'commands':rows[:limit],'excluded':excluded,'note':'按当前模式可尝试的静态代码清单，不是可用数据库保证。网络按查询实际结果短暂跳过；文件、依赖及源站身份仍需满足。先help再查询；失败时继续其他来源，不自动申请账号。','setup':setup.status()}

def call(name,a):
    spec=next((t for t in TOOLS if t['name']==name),None)
    if not spec:raise ValueError('未知工具')
    schema=spec['inputSchema']
    if not isinstance(a,dict) or set(a)-schema['properties'].keys() or any(k not in a for k in schema['required']):raise ValueError('参数字段无效')
    if name=='research_setup':
        action=a['action']
        if action=='status':return setup.status()
        if action=='next':return setup.next_step(a.get('source'))
        if action=='select':return setup.select(a.get('mode'))
        if action=='mark':
            if not a.get('step'):raise ValueError('mark需要step')
            return setup.mark(a.get('source'),a['step'])
        if action=='skip':return setup.mark(a.get('source'),skip=True)
        if action=='pause':return setup.pause(True)
        if action=='resume':return setup.pause(False)
        if action=='network_status':return network_health.status()
        if action=='network_reset':return network_health.reset()
        raise ValueError('未知配置动作')
    if name=='research_discover':return discover(**a)
    if name=='research_help':return query(a['command'],help_only=True)
    if name=='research_query':return query(a['command'],a['args'])
    if name=='research_verify':
        source=a['source']
        if source not in setup.PROVIDERS:raise ValueError('未知来源')
        example=setup.PROVIDERS[source][2]
        if not example:raise ValueError('该能力需按引导人工适配并实际核验，不能自动宣称通过')
        result=query(example[0],example[1:])
        setup.record_test(source,result.get('ok',False),example)
        return result

def handle(m):
    if not isinstance(m,dict) or m.get('jsonrpc')!='2.0':return None
    ident=m.get('id');method=m.get('method');params=m.get('params') or {}
    if ident is None:return None
    try:
        if not isinstance(params,dict):raise ValueError('params须为对象')
        if method=='initialize':
            version=params.get('protocolVersion','2024-11-05')
            if version not in ('2024-11-05','2025-03-26','2025-06-18'):version='2024-11-05'
            result={'protocolVersion':version,'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'research-database-mcp-public','version':VERSION},'instructions':'先research_setup status。general开放无需个人凭据及机构网络的全部命令；zju增加机构IP命令；login按需配置个人账号/API凭据。starter仅是回归样例。网络不可达自动跳过，继续其他来源；不根据国别或是否有代理武断推定。暂停恢复见AI安装指南.md。不接收密码密钥，不把目录当作可用性证明。'}
        elif method=='ping':result={}
        elif method=='tools/list':result={'tools':TOOLS}
        elif method=='tools/call':
            value=call(params.get('name'),params.get('arguments',{}))
            result={'content':[{'type':'text','text':json.dumps(value,ensure_ascii=False)}],'isError':isinstance(value,dict) and value.get('ok') is False}
        else:return {'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Method not found'}}
        return {'jsonrpc':'2.0','id':ident,'result':result}
    except Exception as exc:
        # Do not leak arbitrary exception repr, tracebacks or credentials through MCP.
        message=str(exc) if isinstance(exc,(ValueError,TypeError,KeyError)) else '本地配置或执行失败，请检查安装及进度文件；不自动清空已有状态。'
        if method=='tools/call':return {'jsonrpc':'2.0','id':ident,'result':{'content':[{'type':'text','text':message}],'isError':True}}
        return {'jsonrpc':'2.0','id':ident,'error':{'code':-32602,'message':'Invalid params'}}

def main():
    for stream in (sys.stdin,sys.stdout):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    for line in sys.stdin:
        try:
            if len(line)>100000:raise ValueError('请求过大')
            response=handle(json.loads(line))
        except (ValueError,json.JSONDecodeError):response={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}
        if response is not None:print(json.dumps(response,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
