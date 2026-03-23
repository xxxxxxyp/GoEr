/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        goer: {
          bg: '#f4f8fb',
          panel: '#eff6ff',
          ink: '#0f172a',
          subtle: '#475569',
          accent: '#0ea5e9',
          mint: '#22c55e',
        },
      },
      boxShadow: {
        halo: '0 20px 45px -28px rgba(14, 165, 233, 0.45)',
      },
      backgroundImage: {
        mesh: 'radial-gradient(circle at 12% 8%, rgba(14,165,233,0.14), transparent 35%), radial-gradient(circle at 88% 12%, rgba(34,197,94,0.14), transparent 35%)',
      },
    },
  },
  plugins: [],
}
