import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const plasticNames = ['PET', 'HDPE', 'LDPE', 'PP', 'PS', 'Other'];
const plasticEmojis = ['🧴', '🥛', '🛍️', '🥤', '☕', '🔬'];

export const Footer = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % plasticNames.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer>
      {/* CTA Section - Cream */}
      <div className="section-cream section-padding">
        <div className="section-container text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-4xl md:text-6xl lg:text-7xl font-black text-site-text-dark tracking-tight mb-8"
          >
            Classify Plastic.
            <br />
            <span className="bg-gradient-to-r from-emerald-600 to-cyan-600 bg-clip-text text-transparent">
              Save the Planet.
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base md:text-lg text-site-text-dark/60 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            AI-powered plastic classification is the key to unlocking a truly circular economy.
            Every correctly classified piece of plastic is a step toward a cleaner world.
          </motion.p>

          <motion.a
            href="#hero"
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="btn-dark !bg-emerald-600 hover:!bg-emerald-700"
          >
            Back to Top ↑
          </motion.a>
        </div>
      </div>

      {/* Bottom Section - Dark with rotating plastic types */}
      <div className="section-dark py-16 md:py-24">
        <div className="section-container text-center">
          <h3 className="text-5xl md:text-7xl lg:text-8xl font-black text-site-text-light tracking-tight mb-8">
            Classify
          </h3>

          {/* Rotating Plastic Type Carousel */}
          <div className="flex justify-center items-center gap-6 mb-6">
            {[-1, 0, 1].map((offset) => {
              const idx = (currentIndex + offset + plasticEmojis.length) % plasticEmojis.length;
              const isCenter = offset === 0;
              return (
                <motion.div
                  key={`${idx}-${offset}`}
                  animate={{
                    scale: isCenter ? 1 : 0.7,
                    opacity: isCenter ? 1 : 0.4,
                  }}
                  transition={{ duration: 0.4 }}
                  className={`bg-white/10 backdrop-blur rounded-2xl flex items-center justify-center ${
                    isCenter ? 'w-28 h-28 md:w-36 md:h-36' : 'w-20 h-20 md:w-24 md:h-24'
                  }`}
                >
                  <span className={isCenter ? 'text-6xl md:text-7xl' : 'text-4xl md:text-5xl'}>
                    {plasticEmojis[idx]}
                  </span>
                </motion.div>
              );
            })}
          </div>

          <motion.p
            key={currentIndex}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-3xl md:text-5xl font-black text-emerald-400"
          >
            {plasticNames[currentIndex]}
          </motion.p>
        </div>
      </div>

      {/* Very Bottom Bar */}
      <div className="bg-site-dark border-t border-gray-800 py-4">
        <div className="section-container text-center">
          <p className="text-[10px] md:text-xs tracking-[0.2em] uppercase text-site-text-muted font-medium">
            AI-Powered Plastic Waste Classification System • Built for Sustainable Recycling
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
