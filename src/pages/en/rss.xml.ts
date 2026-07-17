// RSS английской части блога: /en/rss.xml
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { en } from '../../i18n/en';

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ id }) => id.startsWith('en/')))
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
  return rss({
    title: en.blogPage.rssTitle,
    description: en.blogPage.desc,
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/en/blog/${post.id.split('/')[1]}/`,
    })),
    customData: '<language>en</language>',
  });
}
