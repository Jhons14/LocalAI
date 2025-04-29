import typography from '@tailwindcss/typography';

exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,astro}', // adaptá esto según tu estructura
  ],
  theme: {
    darkMode: 'class', // o 'media' si prefieres

    extend: {
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        blink: 'blink 1s step-start infinite',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'slide-up': 'slideUp 0.3s ease-out forwards',
      },
    },
  },
  plugins: [typography, require('tailwind-scrollbar')],
};
