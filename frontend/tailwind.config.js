/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'site-black': '#000000',
        'site-dark': '#1a1a1a',
        'site-dark-surface': '#1c1917',
        'site-cream': '#f9f6f1',
        'site-cream-dark': '#e8e4dc',
        'site-red': '#eb3223',
        'site-red-dark': '#c41f13',
        'site-cta': '#d4e157',
        'site-cta-hover': '#c0ca33',
        'site-text-light': '#f2efea',
        'site-text-muted': '#a0998e',
        'site-text-dark': '#1a1a1a',
        'site-blue-glow': '#1a3a8a',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'hero': ['clamp(3.5rem, 10vw, 8rem)', { lineHeight: '0.95', fontWeight: '900' }],
        'section-title': ['clamp(2rem, 5vw, 4rem)', { lineHeight: '1.1', fontWeight: '900' }],
        'large-body': ['clamp(1.5rem, 3vw, 2.5rem)', { lineHeight: '1.3', fontWeight: '800' }],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'scale-in': 'scaleIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.6s ease-out forwards',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(212, 225, 87, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(212, 225, 87, 0.6)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(40px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
