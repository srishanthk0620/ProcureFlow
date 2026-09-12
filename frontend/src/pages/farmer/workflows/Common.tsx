import { PageVisual } from '../PageVisual'
import { Link, useNavigate } from 'react-router-dom'
import { useFarmerLanguage as useLanguage } from '../useFarmerLanguage'
import type { TranslationKey } from '../../../i18n/translations'
export function WorkflowHeader({title}:{title:TranslationKey}){const {t}=useLanguage();const navigate=useNavigate();return <><div className="pf-workflow-nav"><button className="fh-text-link" onClick={()=>{if(window.history.state?.idx>0)navigate(-1);else navigate('/farmer')}}>← {t('wfBack')}</button><Link className="fh-text-link" to="/farmer">{t('home')}</Link></div><PageVisual title={title}/></>}
export function CommoditySelect({value,onChange}:{value:string;onChange:(value:string)=>void}){const {t}=useLanguage();return <label className="wf-field">{t('commodity')}<select value={value} onChange={e=>onChange(e.target.value)}><option value="paddy">{t('paddy')}</option><option value="copra">{t('wfCopra')}</option></select></label>}

