// Счётчик «без инцидентов» на главной. Импортируется и при сборке (SSR-значение
// в HTML), и в клиентский скрипт Home.astro, который обновляет число по дате
// посетителя — статичный HTML между деплоями не устаревает.

/** Дата последнего инцидента: 2026-07-18 счётчик показывал 214 дней. */
export const incidentFreeSince = '2025-12-16';

export const daysSince = (iso: string, now = new Date()): number =>
  Math.max(0, Math.floor((now.getTime() - new Date(`${iso}T00:00:00`).getTime()) / 86_400_000));

const ruDaysWord = (n: number): string => {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return 'день';
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return 'дня';
  return 'дней';
};

export const formatDays = (n: number, locale: 'ru' | 'en'): string =>
  locale === 'ru' ? `${n} ${ruDaysWord(n)}` : `${n} ${n === 1 ? 'day' : 'days'}`;
