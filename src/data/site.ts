// Бренд и контакты — общие для всех языков. Контент секций живёт в src/i18n/{ru,en}.ts.
// Прайс и комбо-скидки — в src/data/pricing.ts.

export const brand = 'OPSMITH';

export const contacts = {
  name: 'Данила',
  username: 'sugarisbad',
  email: 'contact@opsmith.ru',
  // Бот приёма заявок (см. bot/README.md). Метки источника в payload /start:
  // src-home, src-cases, src-work, custom, calc-<коды>; EN-варианты — с суффиксом -en.
  botUrl: 'https://t.me/sugarisbad_bot',
  calendlyUrl: 'https://calendly.com/opsmith/30min',
};
