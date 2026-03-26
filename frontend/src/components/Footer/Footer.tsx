import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const plasticNames = ['PET', 'HDPE', 'LDPE', 'PP', 'PS', 'PVC'];
const plasticImages = [
  '/images/pet.png',
  '/images/hdpe.png',
  '/images/ldpe.png',
  '/images/pp.png',
  '/images/ps.png',
  '/images/pvc.png',
];

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
            <span className="bg-gradient-to-r from-[#7ed957] to-[#7ed957] bg-clip-text text-transparent">
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
            className="btn-dark !bg-[#7ed957] hover:!bg-[#5cb83f]"
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
              const idx = (currentIndex + offset + plasticImages.length) % plasticImages.length;
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
                  <img
                    src={plasticImages[idx]}
                    alt={plasticNames[idx]}
                    className="w-full h-full object-cover rounded-2xl"
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).style.display = 'none';
                      (e.currentTarget.nextSibling as HTMLElement).style.display = 'flex';
                    }}
                  />
                  <div
                    style={{ display: 'none' }}
                    className="w-full h-full flex-col items-center justify-center gap-1.5"
                  >
                    <svg
                      width={isCenter ? 28 : 20}
                      height={isCenter ? 28 : 20}
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="rgba(255,255,255,0.35)"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <path d="M21 15l-5-5L5 21" />
                    </svg>
                    <span
                      style={{
                        fontSize: isCenter ? 11 : 9,
                        color: 'rgba(255,255,255,0.3)',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                      }}
                    >
                      {plasticNames[idx]}.jpg
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>

          <motion.p
            key={currentIndex}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
            className="text-6xl md:text-7xl font-black text-[#7ed957]"
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
