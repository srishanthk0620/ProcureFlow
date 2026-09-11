import { staffTranslations,type StaffKey } from './staffTranslations'
import { workflowTranslations, type WorkflowKey } from './workflowTranslations'
import { homeTranslations, type HomeKey } from './homeTranslations'
import { authTranslations, type AuthKey } from './authTranslations'
export const languages = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'ml', label: 'മലയാളം' },
] as const
export type Language = typeof languages[number]['code']
const en = {
  home: 'Home', backHome: 'Back home', help: 'Help', demo: 'Demo', language: 'Language',
  skip: 'Skip to content', overview: 'Overview', token: 'My token', circle: 'Farmer Circle',
  journey: 'Journey', operations: 'Operations', resources: 'Resources', centres: 'Centres', monitoring: 'Monitoring',
  farmer: 'Farmer', staff: 'Centre Staff', admin: 'Administrator',
  storageWarning: 'Language changed for this visit. Your browser could not save the preference.',
} as const
export type TranslationKey = keyof typeof en | AuthKey | HomeKey | WorkflowKey | StaffKey
export const translations: Record<Language, Partial<Record<TranslationKey, string>>> = {
  en,
  hi: { home: 'होम', backHome: 'होम पर वापस जाएँ', help: 'सहायता', demo: 'डेमो', language: 'भाषा', skip: 'मुख्य सामग्री पर जाएँ', overview: 'अवलोकन', token: 'मेरा टोकन', circle: 'किसान समूह', journey: 'यात्रा', operations: 'संचालन', resources: 'संसाधन', centres: 'केंद्र', monitoring: 'निगरानी', farmer: 'किसान', staff: 'केंद्र कर्मचारी', admin: 'प्रशासक' },
  kn: { home: 'ಮುಖಪುಟ', backHome: 'ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ', help: 'ಸಹಾಯ', demo: 'ಡೆಮೊ', language: 'ಭಾಷೆ', skip: 'ಮುಖ್ಯ ವಿಷಯಕ್ಕೆ ಹೋಗಿ', overview: 'ಅವಲೋಕನ', token: 'ನನ್ನ ಟೋಕನ್', circle: 'ರೈತರ ಬಳಗ', journey: 'ಪ್ರಯಾಣ', operations: 'ಕಾರ್ಯಾಚರಣೆಗಳು', resources: 'ಸಂಪನ್ಮೂಲಗಳು', centres: 'ಕೇಂದ್ರಗಳು', monitoring: 'ಮೇಲ್ವಿಚಾರಣೆ', farmer: 'ರೈತ', staff: 'ಕೇಂದ್ರ ಸಿಬ್ಬಂದಿ', admin: 'ನಿರ್ವಾಹಕ' },
  ta: { home: 'முகப்பு', backHome: 'முகப்புக்குத் திரும்பு', help: 'உதவி', demo: 'செயல்விளக்கம்', language: 'மொழி', skip: 'முக்கிய உள்ளடக்கத்திற்குச் செல்', overview: 'கண்ணோட்டம்', token: 'எனது டோக்கன்', circle: 'விவசாயிகள் வட்டம்', journey: 'பயணம்', operations: 'செயல்பாடுகள்', resources: 'வளங்கள்', centres: 'மையங்கள்', monitoring: 'கண்காணிப்பு', farmer: 'விவசாயி', staff: 'மைய ஊழியர்கள்', admin: 'நிர்வாகி' },
  ml: { home: 'മുഖപ്പേജ്', backHome: 'മുഖപ്പേജിലേക്ക് മടങ്ങുക', help: 'സഹായം', demo: 'ഡെമോ', language: 'ഭാഷ', skip: 'പ്രധാന ഉള്ളടക്കത്തിലേക്ക് പോകുക', overview: 'അവലോകനം', token: 'എന്റെ ടോക്കൺ', circle: 'കർഷക കൂട്ടായ്മ', journey: 'യാത്ര', operations: 'പ്രവർത്തനങ്ങൾ', resources: 'വിഭവങ്ങൾ', centres: 'കേന്ദ്രങ്ങൾ', monitoring: 'നിരീക്ഷണം', farmer: 'കർഷകൻ', staff: 'കേന്ദ്ര ജീവനക്കാർ', admin: 'അഡ്മിനിസ്ട്രേറ്റർ' },
}
export function isLanguage(value: unknown): value is Language {
  return languages.some(language => language.code === value)
}
export function translate(language: Language, key: TranslationKey): string {
  if (key in staffTranslations.en) return staffTranslations[language]?.[key as StaffKey] ?? staffTranslations.en[key as StaffKey]
  if (key in workflowTranslations.en) return workflowTranslations[language]?.[key as WorkflowKey] ?? workflowTranslations.en[key as WorkflowKey]
  if (key in homeTranslations.en) return homeTranslations[language]?.[key as HomeKey] ?? homeTranslations.en[key as HomeKey]
  if (key in authTranslations.en) return authTranslations[language]?.[key as AuthKey] ?? authTranslations.en[key as AuthKey]
  return translations[language]?.[key] ?? en[key as keyof typeof en]
}




