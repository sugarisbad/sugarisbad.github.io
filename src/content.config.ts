// Коллекция статей блога. Файлы: src/content/blog/{ru,en}/<slug>.md —
// одинаковый slug в обеих локалях даёт зеркальные URL /blog/<slug>/ и /en/blog/<slug>/.
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    /** Заголовок без разметки — для <title>, списков, RSS. */
    title: z.string(),
    /** Заголовок с <em>-акцентом для H1 статьи (опционально). */
    titleHtml: z.string().optional(),
    /** Короткий excerpt: description страницы, лид статьи, текст в списке и RSS. */
    description: z.string(),
    pubDate: z.date(),
    /** Категория для фильтра на списке блога (id из blogPage.cats). */
    cat: z.enum(['vps', 'docker', 'monitoring', 'cicd', 'ai']),
    tags: z.array(z.string()),
    /** Время чтения в минутах. */
    minutes: z.number(),
    /** Переопределение CTA-карточки в конце статьи (иначе — общие тексты из i18n). */
    ctaTitle: z.string().optional(),
    ctaText: z.string().optional(),
  }),
});

export const collections = { blog };
