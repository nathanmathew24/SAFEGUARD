/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#dde6ff',
          500: '#3b5fc0',
          600: '#1a3c5e',
          700: '#162f4a',
          900: '#0d1e30',
        },
      },
    },
  },
  plugins: [],
};
