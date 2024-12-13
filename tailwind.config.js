/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.css',
    "./src/**/*.{html,js}",
  ],
  theme: {
    extend: {colors: {
        cyan: {
          600: '#0891b2',
        },
      },
    },
  },
  plugins: [],
}

