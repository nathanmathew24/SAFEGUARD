import React, { createContext, useContext, useState, ReactNode } from 'react';

type Lang = 'en' | 'ar';

interface LangContextValue {
  lang: Lang;
  toggle: () => void;
  t: (en: string, ar: string) => string;
  dir: 'ltr' | 'rtl';
}

const LangContext = createContext<LangContextValue | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('en');

  const toggle = () => setLang((l) => (l === 'en' ? 'ar' : 'en'));
  const t = (en: string, ar: string) => (lang === 'ar' ? ar : en);
  const dir = lang === 'ar' ? 'rtl' : 'ltr';

  return (
    <LangContext.Provider value={{ lang, toggle, t, dir }}>
      <div dir={dir} lang={lang} className={lang === 'ar' ? 'font-arabic' : ''}>
        {children}
      </div>
    </LangContext.Provider>
  );
}

export function useLang(): LangContextValue {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error('useLang must be used inside LangProvider');
  return ctx;
}
