/** 同一 CADAL 特藏首屏响应的数量校验。 */
export function validateCadalResponseCounts(d){
 if(d?.code!==200||!Number.isSafeInteger(d.data?.total)||d.data.total<0||!Array.isArray(d.data?.dataTablemaps)||d.data.dataTablemaps.length>30||d.data.dataTablemaps.length>d.data.total)throw Error('站方题录响应数量异常');
}
