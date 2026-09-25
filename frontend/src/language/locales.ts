import { en } from "./lang/en.lang";

// locales.ts
export interface Locale {
  greeting: string;
  farewell: string;
  welcomeMessage: string;
  buttonText: string;
}

export type Languages = { [key: string]: Locale };

export const languages: Languages = {
  en: en,
};

export const LANG = languages['en'];