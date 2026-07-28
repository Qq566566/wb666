import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ pattern: '**/[^_]*.md', base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string().default(''),
    pubDate: z.union([z.string(), z.date()]).transform((val) => {
      const parsed = new Date(val);
      return isNaN(parsed.getTime()) ? new Date() : parsed;
    }),
    category: z.string().optional(),
    image: z.string().optional(),     // 允许接收动态图片 URL
    heroImage: z.string().optional(), // 允许接收动态封面图 URL
  }),
});

export const collections = { blog };
