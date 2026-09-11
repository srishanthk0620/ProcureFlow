import { Link } from 'react-router-dom'
import { useLanguage } from '../../../i18n/languageState'
import type { TranslationKey } from '../../../i18n/translations'
export function WorkflowHeader({title}:{title:TranslationKey}){const {t}=useLanguage();return <><Link className="fh-text-link" to="/farmer">← {t('backHome')}</Link><h1>{t(title)}</h1><p className="wf-demo">{t('wfDemo')}</p></>}
export function CommoditySelect({value,onChange}:{value:string;onChange:(value:string)=>void}){const {t}=useLanguage();return <label className="wf-field">{t('commodity')}<select value={value} onChange={e=>onChange(e.target.value)}><option value="paddy">{t('paddy')}</option><option value="copra">{t('wfCopra')}</option></select></label>}

