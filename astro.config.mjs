import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://blog.wb666.im',
  integrations: [
    sitemap({
      filter: (page) => typeof page === 'string' && page.length > 0,
      serialize(item) {
        if (!item || !item.url) return undefined;
        return item;
      },
    }),
  ],
});
