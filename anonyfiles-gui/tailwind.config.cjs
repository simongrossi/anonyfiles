/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js,svelte,ts}",
  ],
  darkMode: "class", // Active le dark mode via la classe "dark" sur <body>
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Montserrat', 'ui-sans-serif', 'system-ui'],
        inter: ['Inter', 'ui-sans-serif', 'system-ui'],
        montserrat: ['Montserrat', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        primary: "#1c7ed6", // Bleu principal
        accent: "#74c0fc",  // Bleu clair accent
        // Ajoute d'autres couleurs si besoin
      },
      borderRadius: {
        xl: "1rem",
        '2xl': "1.5rem",
      },
      boxShadow: {
        xl: "0 8px 32px 0 rgba(60, 60, 110, 0.12)",
      },
    },
  },
  plugins: [],
};
