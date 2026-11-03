"""Resumable, per-user configuration. No credentials are accepted by MCP tools."""
import sys
sys.dont_write_bytecode=True
import argparse, getpass, json
from pathlib import Path
import release_runtime as rt

PROVIDERS={
 'eia':('美国能源信息署 EIA','https://www.eia.gov/opendata/register.php',['eia-v2-browse','electricity']),
 'cinii':('CiNii Research','https://support.nii.ac.jp/en/cinii/api/developer',['cinii-research-search','climate','--count','1']),
 'asean':('ASEANstats','https://api.aseanstats.org/login',['aseanstats-query','social-indicators']),
 'undp':('UNDP DataPrism','https://dataprism.hdrdata.org/',['undp-prism-metadata','datasets','--limit','1']),
 'elsevier':('Elsevier Scopus / ScienceDirect','https://dev.elsevier.com/',['elsevier-scopus-structured','climate','--count','1']),
 'wto':('世界贸易组织 WTO','https://apiportal.wto.org/',['wto-indicators','trade']),
 'springer':('Springer Nature Meta','https://dev.springernature.com/',['springer-meta-open','climate','--limit','1']),
 'wos':('Web of Science Starter','https://developer.clarivate.com/',['wos-starter-structured','climate','--limit','1']),
 'iom-baseline':('IOM DTM Baseline','https://dtmapi.iom.int/',['iom-dtm-countries']),
 'iom-hna':('IOM Humanitarian Needs Assessment','https://dtmapi.iom.int/',['iom-hna-countries']),
 'iati':('IATI Datastore','https://developer.iatistandard.org/',['iati-datastore','activity','*:*','--rows','1']),
 'un-population':('联合国人口数据','https://population.un.org/dataportalapi/token/index.html',['un-population-portal-data','49','818','2020','2021']),
 'cas':('CAS Common Chemistry','https://commonchemistry.cas.org/api',['cas-common-search','water','--size','1']),
 'institution':('用户自己的机构订阅及浏览器会话','',None),
 'public-files':('需要官方PDF表格的扩展功能','',None),
 'other-keys':('其他可选API环境变量','',None),
}
STEPS=['read_terms','account_ready','credential_issued','credential_saved','tested']
GUIDE={
 'read_terms':'打开官方说明核对权限、用途和条款；有协议、费用、验证或权限提示时由用户决定，AI不能代替声明已阅读。',
 'account_ready':'如该来源要求账号，让用户使用自己的邮箱注册并完成邮件验证或登录。已有账号直接使用，不重复注册。',
 'credential_issued':'在官方门户申请并获取该来源的API凭据；网页可登录不等于API获批。有审批则记录等待并先配置其他来源。',
 'credential_saved':'用户在本机终端运行 python onboarding.py credential SOURCE，隐藏输入自己的密钥；不要把密钥发到聊天或写进源码。',
 'tested':'先从目录发现合法参数，再做少量真实查询；必须取得有效返回才算验证通过。帮助页面成功不能算接口验证。',
}

def status():
    s=rt.load_state();return {'mode':s['mode'],'needs_choice':s['mode'] is None,'paused':s.get('paused',False),'active_source':s.get('active_source'),'progress':s['progress'],'state_location':str(rt.state_root()),'notice':'全部功能表示逐步配置本包可选能力，不等于每个数据库已授权或全量可用。'}

def select(mode):
    if mode not in ('partial','full'):raise ValueError('mode 须为 partial 或 full')
    s=rt.load_state();s['mode']=mode;s['paused']=False;rt.save_state(s)
    return status()

def next_step(source=None):
    s=rt.load_state()
    if source is not None:
        if source not in PROVIDERS:raise ValueError('未知来源')
        s['active_source']=source
        if source in s['progress']:s['progress'][source]['skipped']=False
        rt.save_state(s)
    if s.get('paused'):return {'action':'paused','message':'配置进度已保存；已有功能可以继续使用。下次调用 research_setup(action="resume") 即可继续。'}
    if s['mode'] is None:return {'action':'ask_mode','question':'使用免登录的部分功能，还是逐步配置全部可选功能？','choices':['partial','full']}
    if s['mode']=='partial':return {'action':'ready','message':'免登录模式可直接查询起步公共来源；可随时切换full，原配置进度仍保留。'}
    active=s.get('active_source')
    candidates=[source] if source else ([active] if active in PROVIDERS else [])+[key for key in PROVIDERS if key!=active]
    for key in candidates:
        if key not in PROVIDERS:raise ValueError('未知来源')
        saved=s['progress'].get(key,{})
        if saved.get('skipped') and not source:continue
        name,url,example=PROVIDERS[key]
        if key in ('institution','public-files','other-keys'):
            if saved.get('completed'):continue
            detail={'institution':'先询问用户自己的学校或机构；通过该机构官方数据库目录打开来源并验证IP或机构登录。浏览器代码含部分学校专用断言，不可直接当作别的学校可用，需按页面适配并真实检索。会话不随包迁移。','public-files':'命令标有may_need_public_file时先读 --help 和对应模块的官方来源链接。由用户提供公开文件路径或从官方重新获取，不恢复发送者的历史材料，不把缺文件算零结果。','other-keys':'这些功能只读取 RESEARCH_MCP_EXTERNAL_ 前缀的专用环境变量；变量名在对应适配器中查看。不要导入任何发送者或其他应用的环境配置。'}[key]
            return {'source':key,'name':name,'step':'manual_validation','instruction':detail}
        for step in STEPS:
            if step in saved.get('done',[]):continue
            return {'source':key,'name':name,'url':url,'step':step,'instruction':GUIDE[step].replace('SOURCE',key),'special':'ASEANstats要求先启用双重验证；用用户自己的邮箱或验证器。' if key=='asean' else '', 'test_example':example if step=='tested' else None,'can_pause':True,'can_skip':True}
    return {'action':'configured','message':'所选步骤已记录完成或跳过；记录不替代源站实时验证，未配置来源仍不可用。'}

def mark(source,step=None,skip=False):
    if source not in PROVIDERS:raise ValueError('未知来源')
    if step not in STEPS+[None,'manual_validation']:raise ValueError('未知步骤')
    s=rt.load_state();p=s['progress'].setdefault(source,{'done':[]});p['skipped']=bool(skip)
    s['active_source']=None if skip else source
    if step:
        if step=='tested':raise ValueError('请通过 research_verify 执行真实查询，不能用确认动作代替测试')
        if step=='manual_validation':p['completed']=True;p['evidence_kind']='user_or_agent_confirmation'
        elif step not in p['done']:p['done'].append(step)
    rt.save_state(s);return next_step(source) if not skip else status()

def record_test(source,success,command):
    if source not in PROVIDERS:raise ValueError('未知来源')
    s=rt.load_state();p=s['progress'].setdefault(source,{'done':[]});p['last_test']={'success':bool(success),'command':command,'kind':'actual_command_execution'}
    if success and 'tested' not in p['done']:p['done'].append('tested')
    rt.save_state(s)

def pause(paused=True):
    s=rt.load_state();s['paused']=paused;rt.save_state(s)
    return status() if paused else next_step()

def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('status');sub.add_parser('next');p=sub.add_parser('mode');p.add_argument('mode',choices=['partial','full'])
    p=sub.add_parser('credential');p.add_argument('source',choices=[k for k in PROVIDERS if k not in ('institution','public-files','other-keys')])
    a=parser.parse_args()
    if a.action=='status':r=status()
    elif a.action=='next':r=next_step()
    elif a.action=='mode':r=select(a.mode)
    else:
        value=getpass.getpass('请输入你自己的接口凭据（不回显，不写入项目）：')
        rt.save_credential(a.source,value)
        if not rt.credential(a.source):raise RuntimeError('保存后读取验证失败，请勿重复创建令牌')
        r=mark(a.source,'credential_saved')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
