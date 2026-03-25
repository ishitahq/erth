import { motion } from 'framer-motion';
import { featuresData } from '../../data/chatbotData';

export const FeaturesSection = () => {
  const coreFeatures = featuresData.filter((f) => f.type === 'core');
  const optionalFeatures = featuresData.filter((f) => f.type === 'optional');

  return (
    <section id="features" className="section-dark section-padding">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 md:mb-20"
        >
          <p className="text-emerald-400 text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            Capabilities
          </p>
          <h2 className="heading-section mb-6">
            Built for Real-World
            <br />
            <span className="text-site-text-muted">Recycling Challenges</span>
          </h2>
        </motion.div>

        {/* Core Features */}
        <div className="mb-16">
          <motion.h3
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-sm uppercase tracking-widest text-emerald-400 font-bold mb-8"
          >
            Core Features
          </motion.h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {coreFeatures.map((feature, index) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/8 hover:border-emerald-500/30 transition-all duration-300 group"
              >
                <div className="flex items-start gap-4">
                  <span className="text-3xl group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </span>
                  <div>
                    <h4 className="text-lg font-bold text-site-text-light mb-2 group-hover:text-emerald-400 transition-colors">
                      {feature.title}
                    </h4>
                    <p className="text-sm text-site-text-muted leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Optional Enhancements */}
        <div>
          <motion.h3
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-sm uppercase tracking-widest text-cyan-400 font-bold mb-8"
          >
            Optional Enhancements
          </motion.h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {optionalFeatures.map((feature, index) => (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-6 hover:bg-white/[0.06] hover:border-cyan-500/30 transition-all duration-300 group"
              >
                <div className="flex items-start gap-4">
                  <span className="text-3xl opacity-70 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300">
                    {feature.icon}
                  </span>
                  <div>
                    <h4 className="text-lg font-bold text-site-text-light/80 mb-2 group-hover:text-cyan-400 transition-colors">
                      {feature.title}
                    </h4>
                    <p className="text-sm text-site-text-muted/80 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
