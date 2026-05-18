import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50:  '#f7f7f6',
          100: '#eeede9',
          200: '#d3d1c7',
          300: '#b4b2a9',
          400: '#888780',
          500: '#5f5e5a',
          600: '#444441',
          700: '#2c2c2a',
          800: '#1a1a18',
          900: '#0e0e0d',
        },
        status: {
          green: '#1d9e75',
          amber: '#ba7517',
          red:   '#a32d2d',
          blue:  '#185fa5',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        xs:   ['12px', { lineHeight: '1.5' }],
        sm:   ['14px', { lineHeight: '1.5' }],
        base: ['14px', { lineHeight: '1.5' }],
        lg:   ['16px', { lineHeight: '1.5' }],
        xl:   ['18px', { lineHeight: '1.5' }],
      },
    },
  },
  plugins: [],
} satisfies Config
