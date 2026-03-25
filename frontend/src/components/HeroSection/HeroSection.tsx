import { motion } from 'framer-motion';

const words = [
  { text: 'Classify.', gradient: false },
  { text: 'Recycle.', gradient: true },
  { text: 'Sustain.', gradient: false },
];

export const HeroSection = () => {
  return (
    <section id="hero" className="section-dark min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background image overlay */}
      <div
        className="absolute inset-0 opacity-15 bg-cover bg-center"
        style={{ backgroundImage: 'url(/hero-plastic.png)' }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/80 to-black" />

      <div className="section-container text-center py-4 md:py-6 lg:py-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-4"
        >
          <img src="/images/1.png" alt="erth logo" className="w-16 h-16 md:w-20 md:h-20 mb-2 mx-auto" />
        </motion.div>

        <h1 className="heading-hero mb-6 md:mb-8 flex items-center justify-center gap-x-3 md:gap-x-4 lg:gap-x-5 whitespace-nowrap text-[clamp(2rem,6vw,3.5rem)] md:text-[clamp(2.5rem,7vw,4.5rem)] lg:text-[clamp(3rem,8vw,5.5rem)] leading-tight">
          {words.map((word, index) => (
            <motion.span
              key={word.text}
              initial={{ opacity: 0, y: -80 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.7,
                delay: index * 0.25,
                ease: [0.34, 1.56, 0.64, 1], // spring-like bounce
              }}
              className={
                word.gradient
                  ? 'bg-gradient-to-r from-[#7ed957] to-[#7ed957] bg-clip-text text-transparent inline-block'
                  : 'inline-block'
              }
            >
              {word.text}
            </motion.span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9, ease: 'easeOut' }}
          className="text-sm md:text-base lg:text-lg text-site-text-muted max-w-2xl mx-auto mb-8 md:mb-10 leading-relaxed"
        >
          An AI-powered system that automatically classifies plastic waste into specific
          types using images, enabling smarter recycling, reducing contamination, and
          building a circular economy.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.2 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <a href="#features" className="btn-cta !bg-[#7ed957] hover:!bg-[#5cb83f] !shadow-[#7ed957]/30 hover:!shadow-[#7ed957]/50">
            Explore Features
          </a>
          <a href="#plastic-types" className="btn-dark !bg-white/10 !border !border-white/20 backdrop-blur hover:!bg-white/20">
            View Plastic Types
          </a>
        </motion.div>
      </div>

    </section>
  );
};

export default HeroSection;
