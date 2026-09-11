import { useEffect, useState, type ReactNode } from 'react'
import { translate, type Language } from './translations'
import { LanguageContext, persistLanguage, readLanguage, type LanguageState } from './languageState'
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LanguageState>(readLanguage)
  useEffect(() => { document.documentElement.lang = state.language }, [state.language])
  function setLanguage(language: Language) {
    setState(persistLanguage(language))
  }
  return <LanguageContext.Provider value={{ ...state, setLanguage, t: key => translate(state.language, key) }}>{children}</LanguageContext.Provider>
}


