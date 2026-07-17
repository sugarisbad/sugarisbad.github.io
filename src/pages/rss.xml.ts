// RSS русской части блога: /rss.xml
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { ru } from '../i18n/ru';

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ id }) => id.startsWith('ru/')))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
  return rss({
    title: ru.blogPage.rssTitle,
    description: ru.blogPage.desc,
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/blog/${post.id.split('/')[1]}/`,
    })),
    customData: '<language>ru</language>',
  });
}
