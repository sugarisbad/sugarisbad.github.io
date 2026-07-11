// Бренд и контакты — общие для всех языков. Контент секций живёт в src/i18n/{ru,en}.ts.

export const brand = 'opsmith';

export const contacts = {
  name: 'Данила',
  username: 'sugarisbad',
  email: 'dk0x@proton.me',
  telegram: 'sugarisbaddy',
  telegramUrl: 'https://t.me/sugarisbaddy',
  github: 'sugarisbad',
  githubUrl: 'https://github.com/sugarisbad',
  // Бот приёма заявок (см. bot/README.md).
  botUrl: 'https://t.me/sugarisbad_bot',
};

// Однобуквенные коды позиций прайса для payload калькулятора
// (t.me/<bot>?start=calc-<коды>, максимум 64 символа [A-Za-z0-9_-]).
// Должны совпадать с CALC_ITEMS в bot/bot.py.
export const calcCodes: Record<string, string> = {
  'vps-setup': 'a',
  'audit': 'b',
  'nginx-ssl': 'c',
  'migration': 'd',
  'backup': 'e',
  'dockerize': 'f',
  'compose': 'g',
  'cicd': 'h',
  'mass-deploy': 'i',
  'monitoring': 'j',
  'balancer': 'k',
  'failover': 'l',
  'ollama': 'm',
  'tg-bot': 'n',
  'turnkey': 'o',
  'subscription': 'p',
  'consult': 'q',
  'incident': 'r',
};
