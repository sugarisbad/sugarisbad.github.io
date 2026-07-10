// Локали и хелперы маршрутов. Русский — на корне, английский — под /en/.
import { ru, type Dict, type Locale } from './ru';
import { en } from './en';

export type { Dict, Locale };
export const locales: Locale[] = ['ru', 'en'];
export const defaultLocale: Locale = 'ru';

const dicts: Record<Locale, Dict> = { ru, en };
export const t = (locale: Locale): Dict => dicts[locale];

/** Ссылка на страницу `path` (без префикса локали, напр. '' или 'cases/') в заданной локали. */
export const localeUrl = (locale: Locale, path: string, base = '/'): string =>
  locale === defaultLocale ? `${base}${path}` : `${base}en/${path}`;
