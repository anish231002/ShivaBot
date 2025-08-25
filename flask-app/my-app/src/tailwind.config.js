/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,html}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Light theme colors (matching your image)
        headerBg: '#ff7b00',
        mainBg: '#FFF8E1',
        chatBg: '#FFFFFF',
        borderColor: '#E0E0E0',
        textColor: '#333333',
        secondaryTextColor: '#666666',
        accentColor: '#ff7b00',
        buttonBgColor: '#F0F0F0',
        redEndCall: '#DC3545',
        greenStatus: '#28A745',
        videoArea: '#c48e6f',
        
        // Dark theme colors
        headerBgDark: '#ec940e',
        mainBgDark: '#181818',
        chatBgDark: '#222222',
        borderColorDark: '#444444',
        textColorDark: '#f5f5f5',
        secondaryTextColorDark: '#bbbbbb',
        accentColorDark: '#FFA500',
        buttonBgColorDark: '#333333',
      },
      fontFamily: {
        devanagari: ['Noto Sans Devanagari', 'Mangal', 'Arial', 'sans-serif'],
      },
      spacing: {
        '7.5': '1.875rem', // 30px
      },
      flex: {
        '3': '3',
        '5': '5',
      },
      boxShadow: {
        'user-video': '0 2px 5px rgb(158, 104, 41)',
        'video-placeholder': '0 0 15px rgba(0, 0, 0, 0.3)',
      }
    },
  },
  plugins: [],
}
