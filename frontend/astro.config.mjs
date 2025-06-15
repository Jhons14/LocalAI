// @ts-check
import { defineConfig } from 'astro/config';
import svgr from 'vite-plugin-svgr';

import tailwindcss from '@tailwindcss/vite';

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  vite: {
    plugins: [tailwindcss(), svgr()],
    preview: {
      allowedHosts: ['.ngrok-free.app'], // o el dominio exacto que te dio ngrok
    },
    server: {
      allowedHosts: ['.ngrok-free.app'],
    },
  },

  integrations: [react()],
});
