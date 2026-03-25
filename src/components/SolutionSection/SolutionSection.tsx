import { useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const fullText =
  'Using deep learning and computer vision, we can automatically classify plastic waste into specific types with high accuracy — even when plastic is dirty, deformed, or mixed. This enables faster, more reliable recycling at scale.';

export const SolutionSection = () => {
  const textRef = useRef<HTMLDivElement>(null);
  const sectionRef = useRef<HTMLElement>(null);
  const [revealProgress, setRevealProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      if (!sectionRef.current) return;
      const rect = sectionRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;

      // Start revealing when section enters viewport, complete when section is centered
      const sectionTop = rect.top;
      const sectionHeight = rect.height;

      // Calculate progress: 0 when section top enters viewport, 1 when section is fully scrolled through
      const start = windowHeight * 0.8;
      const end = -sectionHeight * 0.3;
      const progress = Math.min(1, Math.max(0, (start - sectionTop) / (start - end)));

      setRevealProgress(progress);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Initial check
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Split text into individual characters for per-character reveal
  const chars = fullText.split('');

  return (
    <section
      ref={sectionRef}
      id="solution"
      className="section-dark section-padding relative overflow-hidden"
    >
      {/* Background AI image */}
      <div
        className="absolute inset-0 opacity-10 bg-cover bg-center"
        style={{ backgroundImage: 'url(/ai-classification.png)' }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black via-black/90 to-black" />

      <div className="section-container relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="text-center max-w-5xl mx-auto"
        >
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-emerald-400 text-sm md:text-base uppercase tracking-widest mb-6 font-semibold"
          >
            The Solution
          </motion.p>

          <h2 className="text-section-title md:text-[clamp(2.5rem,5vw,4.5rem)] font-black leading-tight mb-8">
            <span className="text-site-text-light">AI can solve</span>
            <br />
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              this crisis.
            </span>
          </h2>

          {/* Scroll-reveal text: grey → white character by character */}
          <div
            ref={textRef}
            className="mt-8 md:mt-12 text-xl md:text-2xl lg:text-3xl leading-relaxed max-w-4xl mx-auto font-medium"
          >
            {chars.map((char, i) => {
              const charProgress = i / chars.length;
              const isRevealed = revealProgress > charProgress;
              return (
                <span
                  key={i}
                  style={{
                    color: isRevealed ? '#f2efea' : 'rgba(255,255,255,0.25)',
                    transition: 'color 0.15s ease',
                  }}
                >
                  {char}
                </span>
              );
            })}
          </div>

          {/* Tech stack badges */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex flex-wrap gap-3 justify-center mt-12"
          >
            {['CNN', 'Transfer Learning', 'ResNet / EfficientNet', 'Data Augmentation', 'Edge Deployment'].map((tech) => (
              <span
                key={tech}
                className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-xs md:text-sm font-medium"
              >
                {tech}
              </span>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default SolutionSection;
