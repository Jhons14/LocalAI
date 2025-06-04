import typography from '@tailwindcss/typography';
import animate from 'tw-animate-css';

/** @type {import('tailwindcss').Config} */

export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],

  plugins: [animate],
};
