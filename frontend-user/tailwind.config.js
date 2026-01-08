/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 品牌主色 - 基于Logo深青色
        primary: {
          50: '#E8F4F6',
          100: '#D1E9ED',
          200: '#A3D3DB',
          300: '#75BDC9',
          400: '#47A7B7',
          500: '#23586A', // Logo主色
          600: '#1D4A59',
          700: '#173C48',
          800: '#112E37',
          900: '#0B2026',
        },
        // 天蓝强调色 - 参考Epic
        sky: {
          400: '#38BDF8',
          500: '#0095D9',
          600: '#0077B6',
        },
        // 珊瑚粉
        coral: {
          400: '#FF8FAB',
          500: '#FF6B9D',
          600: '#E85A8C',
        },
        // 明黄色
        sunny: {
          400: '#FFE566',
          500: '#FFD93D',
          600: '#F5C518',
        },
        // 薰衣草紫
        lavender: {
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
        },
      },
      fontFamily: {
        sans: ['Nunito', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        display: ['Nunito', 'PingFang SC', 'sans-serif'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'card': '0 8px 30px rgba(0, 0, 0, 0.12)',
        'button': '0 4px 14px rgba(35, 88, 106, 0.4)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'bounce-slow': 'bounce 2s infinite',
        'pulse-soft': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      }
    },
  },
  plugins: [],
}
