import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend'; // To load translations from /public/locales

i18n
  // Load translation using http -> see /public/locales
  // Learn more: https://github.com/i18next/i18next-http-backend
  .use(HttpApi)
  // Detect user language
  // Learn more: https://github.com/i18next/i18next-browser-languageDetector
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next.
  .use(initReactI18next)
  // Init i18next
  // For all options read: https://www.i18next.com/overview/configuration-options
  .init({
    debug: import.meta.env.DEV, // Log i18n activity in development
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // Not needed for react as it escapes by default
    },
    // backend: {
    //   loadPath: '/locales/{{lng}}/{{ns}}.json', // Default path for HttpApi
    // },
    // detection: {
    //   order: ['localStorage', 'navigator', 'htmlTag'],
    //   caches: ['localStorage'],
    // },
  });

export default i18n; 