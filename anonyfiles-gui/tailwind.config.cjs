module.exports = {
  content: [
    "./src/**/*.{html,js,svelte,ts}", // NE PAS OUBLIER le .svelte !
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Montserrat', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        primary: "#1c7ed6",
        accent: "#74c0fc",
      },
      // Ajoute ici tes customs
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    // tu peux enlever si tu ne veux pas ces plugins
  ],
}
