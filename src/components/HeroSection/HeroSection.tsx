import { motion } from 'framer-motion';

export const HeroSection = () => {
  return (
    <section id="hero" className="section-dark min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background image overlay */}
      <div
        className="absolute inset-0 opacity-15 bg-cover bg-center"
        style={{ backgroundImage: 'url(/hero-plastic.png)' }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/80 to-black" />

      <div className="section-container text-center py-20 md:py-32 lg:py-40 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-6"
        >
          <span className="inline-block text-6xl md:text-7xl mb-4">♻️</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="heading-hero mb-8 md:mb-12"
        >
          Classify.
          <br />
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Recycle.
          </span>
          <br />
          Sustain.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: 'easeOut' }}
          className="text-lg md:text-xl lg:text-2xl text-site-text-muted max-w-3xl mx-auto mb-10 md:mb-14 leading-relaxed"
        >
          An AI-powered system that automatically classifies plastic waste into specific
          types using images — enabling smarter recycling, reducing contamination, and
          building a circular economy.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <a href="#features" className="btn-cta !bg-emerald-500 hover:!bg-emerald-600 !shadow-emerald-500/30 hover:!shadow-emerald-500/50">
            Explore Features
          </a>
          <a href="#plastic-types" className="btn-dark !bg-white/10 !border !border-white/20 backdrop-blur hover:!bg-white/20">
            View Plastic Types
          </a>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
          className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center pt-2"
        >
          <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
};

export default HeroSection;
