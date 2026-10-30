/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Foundation Palette
        charcoal: {
          DEFAULT: '#171717',
          bg: '#171717',
          surface: '#202020',
          card: '#1F1F1F',
          subcard: '#252525',
          border: '#343434',
          borderHighlight: '#484848',
        },
        forest: {
          DEFAULT: '#06110C',
          bg: '#06110C',
          surface: '#0B1B14',
          surfaceElevated: '#10261D',
          border: '#20372B',
          borderSubtle: '#15261E',
          hover: '#0E241B',
          glow: 'rgba(32, 55, 43, 0.4)',
        },
        crimson: {
          DEFAULT: '#A31C1B',
          primary: '#A31C1B',
          hover: '#C12A29',
          pressed: '#7F1717',
          light: '#E24A49',
          subtle: 'rgba(163, 28, 27, 0.15)',
          surface: '#261214',
          border: '#5C1D20',
          glow: 'rgba(163, 28, 27, 0.35)',
        },
        themeText: {
          primary: '#F5F2EF',
          secondary: '#B7B3B0',
          muted: '#898582',
        },
        // Unified Dark Token Mappings for Existing Components
        dark: {
          canvas: '#171717',
          surface: '#202020',
          surfaceHover: '#262626',
          card: '#202020',
          subcard: '#171717',
          forestBg: '#06110C',
          forestSurface: '#0B1B14',
          border: '#343434',
          borderForest: '#20372B',
          borderHighlight: '#484848',
          textPrimary: '#F5F2EF',
          textSecondary: '#B7B3B0',
          textMuted: '#898582',
          crimsonPrimary: '#A31C1B',
          crimsonHover: '#C12A29',
          crimsonPressed: '#7F1717',
          crimsonSurface: '#261214',
          crimsonBorder: '#5C1D20',
          crimsonLight: '#E24A49',
          rose: '#FB7185',
          roseMuted: '#F43F5E',
          amber: '#FBBF24',
          emerald: '#34D399',
        },
      }
    },
  },
  plugins: [],
};
