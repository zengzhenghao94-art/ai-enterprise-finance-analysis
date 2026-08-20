/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        steep: {
          obsidian:  '#000000',
          ink:       '#17191c',
          ash:       '#4c4c4c',
          graphite:  '#777b86',
          slate:     '#8b8c8d',
          dove:      '#a3a6af',
          'dove-50': 'rgba(163, 166, 175, 0.5)',
          fog:       '#f7f7f8',
          white:     '#ffffff',
          blue:      '#1e40af',
          cyan:      '#0891b2',
          wash:      '#dbeafe',
          'sky-wash':'#d3e3fc',
          crimson:   '#dc2626',
        },
      },
      fontFamily: {
        display: ['"Noto Serif"', '"Noto Serif CJK SC"', 'SimSun', 'serif'],
        body:    ['Inter', '"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'card': '16px',
        'img':  '12px',
        'btn':  '9999px',
      },
    },
  },
  plugins: [],
}
