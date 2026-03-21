/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:        '#0F172A',
        card:      '#1E293B',
        accent:    '#3B82F6',
        cyan:      '#06B6D4',
        green:     '#22C55E',
        orange:    '#F59E0B',
        danger:    '#EF4444',
        primary:   '#F1F5F9',
        secondary: '#94A3B8',
      },
    },
  },
  plugins: [],
}
