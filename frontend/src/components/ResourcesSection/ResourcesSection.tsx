import { motion } from 'framer-motion';
import { deliverablesData } from '../../data/resourcesData';

export const DeliverablesSection = () => {
  return (
    <section id="deliverables" className="section-dark section-padding">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 md:mb-20"
        >
          <p className="text-emerald-400 text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            Expected Output
          </p>
          <h2 className="heading-section mb-6">
            What We Deliver
          </h2>
          <p className="text-base md:text-lg text-site-text-muted max-w-3xl mx-auto">
            The complete system includes a trained model, documentation, performance metrics,
            and working demonstrations.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {deliverablesData.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -4, scale: 1.02 }}
              className="bg-gradient-to-b from-white/[0.08] to-white/[0.02] border border-white/10 rounded-2xl p-6 hover:border-emerald-500/40 transition-colors duration-300"
            >
              <span className="text-4xl mb-4 block">{item.icon}</span>
              <h3 className="text-lg font-bold text-site-text-light mb-3">
                {item.title}
              </h3>
              <p className="text-sm text-site-text-muted leading-relaxed">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default DeliverablesSection;
