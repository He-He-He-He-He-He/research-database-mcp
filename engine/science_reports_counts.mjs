/** 两地科技报告公共检索首屏的共同响应结构。 */
export function validateScienceReportsCounts(d){const r=d?.RESULT;if(d?.CODE!=='0'||!Number.isSafeInteger(r?.count)||r.count<0||r.pageNo!==1||r.pageSize!==10||!Array.isArray(r.list)||r.list.length>10||r.list.length>r.count)throw Error('科技报告响应结构或总数异常')}
