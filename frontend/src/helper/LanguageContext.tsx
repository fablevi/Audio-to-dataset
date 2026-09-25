// LanguageContext.tsx
import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { type Locale, languages, LANG as DefaultLang } from '../language/locales';

interface LanguageContextType {
  currentLocale: Locale;
  currentLangCode: string;
  setLanguage: (code: string) => void;
  t: (key: keyof Locale) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentLangCode, setCurrentLangCode] = useState<string>('en');
  
  const currentLocale = languages[currentLangCode] || DefaultLang;

  const setLanguage = (code: string) => {
    setCurrentLangCode(code);
  };

  const t = (key: keyof Locale): string => {
    return currentLocale[key];
  };

  return (
    <LanguageContext.Provider value={{ currentLocale, currentLangCode, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export const { LANG: exportedLANG } = { LANG: DefaultLang };