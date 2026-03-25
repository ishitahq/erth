import { motion } from 'framer-motion';

export const SolutionSection = () => {
  return (
    <section id="solution" className="section-dark section-padding relative overflow-hidden">
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

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="mt-8 md:mt-12 body-large max-w-4xl mx-auto"
          >
            <span className="text-site-text-light">
              Using deep learning and computer vision, we can automatically classify
              plastic waste into specific types with high accuracy —
            </span>{' '}
            <span className="text-site-text-muted">
              even when plastic is dirty, deformed, or mixed. This enables faster,
              more reliable recycling at scale.
            </span>
          </motion.p>

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
