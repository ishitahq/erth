import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { plasticTypesData } from '../../data/pyramidData';

export const PlasticTypesSection = () => {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  return (
    <section id="plastic-types" className="section-cream section-padding">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 md:mb-20"
        >
          <p className="text-emerald-600 text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            Classification Categories
          </p>
          <h2 className="heading-section-dark mb-6">
            6 Plastic Types
          </h2>
          <p className="text-base md:text-lg text-site-text-dark/60 max-w-3xl mx-auto">
            The system classifies plastic waste into these categories, each with unique chemical
            properties, recycling methods, and visual characteristics.
          </p>
        </motion.div>

        {/* Plastic Type Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {plasticTypesData.map((plastic, index) => (
            <motion.div
              key={plastic.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group"
            >
              {/* Gradient Top Bar */}
              <div className={`h-2 bg-gradient-to-r ${plastic.color}`} />

              <div className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{plastic.code}</span>
                    <div>
                      <h3 className="text-2xl font-black text-site-text-dark">{plastic.name}</h3>
                      <p className="text-xs text-site-text-dark/50">{plastic.fullName}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full bg-gradient-to-r ${plastic.color} text-white`}>
                    #{plastic.id}
                  </span>
                </div>

                {/* Description */}
                <p className="text-sm text-site-text-dark/70 leading-relaxed mb-4">
                  {plastic.description}
                </p>

                {/* Expandable Details */}
                <button
                  onClick={() => setExpandedId(expandedId === plastic.id ? null : plastic.id)}
                  className="w-full flex items-center justify-between text-sm font-semibold text-site-text-dark/80 hover:text-site-text-dark transition-colors py-2 border-t border-gray-100"
                >
                  <span>Details</span>
                  <motion.div
                    animate={{ rotate: expandedId === plastic.id ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ChevronDown size={16} />
                  </motion.div>
                </button>

                <AnimatePresence>
                  {expandedId === plastic.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-3 space-y-3">
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-site-text-dark/40 font-semibold mb-1">
                            Common Examples
                          </p>
                          <p className="text-sm text-site-text-dark/70">{plastic.examples}</p>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-site-text-dark/40 font-semibold mb-1">
                            Recyclability
                          </p>
                          <p className="text-sm text-site-text-dark/70">{plastic.recyclability}</p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PlasticTypesSection;
