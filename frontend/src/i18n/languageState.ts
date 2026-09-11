import { createContext, useContext } from 'react'
import { isLanguage, type Language, type TranslationKey } from './translations'
export const LANGUAGE_STORAGE_KEY = 'procureflow.language'
export type LanguageState = { language: Language; storageUnavailable: boolean }
type LanguageValue = LanguageState & { setLanguage: (language: Language) => void; t: (key: TranslationKey) => string }
export const LanguageContext = createContext<LanguageValue | undefined>(undefined)

export function readLanguage(): LanguageState {
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
    return { language: isLanguage(stored) ? stored : 'en', storageUnavailable: false }
  } catch {
    // Storage is optional: expose the failure to the UI while preserving in-memory use.
    return { language: 'en', storageUnavailable: true }
  }
}
export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage requires LanguageProvider')
  return context
}

export function persistLanguage(language: Language): LanguageState {
  const next = isLanguage(language) ? language : 'en'
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, next)
    return { language: next, storageUnavailable: false }
  } catch {
    return { language: next, storageUnavailable: true }
  }
}
