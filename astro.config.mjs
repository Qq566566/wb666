import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://blog.wb666.im',
  integrations: [
    sitemap({
      filter: (page) => Boolean(page),
    }),
  ],
});
