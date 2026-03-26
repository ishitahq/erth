import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';
import { statisticsData } from '../../data/statistics';

const AnimatedCounter = ({ target, isVisible }: { target: number; isVisible: boolean }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isVisible) return;
    let startTime: number | null = null;
    const duration = 0.8;

    const animate = (timestamp: number) => {
      if (startTime === null) startTime = timestamp;
      const progress = (timestamp - startTime) / (duration * 1000);
      if (progress < 1) {
        setCount(Math.floor(progress * target));
        requestAnimationFrame(animate);
      } else {
        setCount(target);
      }
    };

    requestAnimationFrame(animate);
  }, [isVisible, target]);

  return <span>{count}</span>;
};

export const StatisticsSection = () => {
  const { ref, isVisible } = useScrollAnimation({ threshold: 0.2 });

  // Compute bar heights proportional to percentages (max percentage = tallest bar)
  const maxPercentage = Math.max(...statisticsData.map((s) => s.percentage));

  return (
    <section id="statistics" className="section-dark" style={{ paddingTop: '5rem', paddingBottom: '1rem' }}>
      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 md:mb-20"
        >
          <p className="text-[#7ed957] text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            The Plastic Crisis
          </p>
          <h2 className="heading-section mb-6">
            The planet is drowning
            <br />
            <span className="text-site-text-muted">in plastic waste.</span>
          </h2>
        </motion.div>

        {/* Bar Stats with scroll-triggered animation */}
        <div ref={ref} className="grid grid-cols-3 gap-4 md:gap-8 items-end mb-16 max-w-5xl mx-auto">
          {statisticsData.map((stat, index) => {
            // Calculate height proportional to percentage value
            const heightPercent = (stat.percentage / maxPercentage) * 100;

            return (
              <motion.div
                key={stat.id}
                initial={{ opacity: 0, scaleY: 0 }}
                animate={isVisible ? { opacity: 1, scaleY: 1 } : { opacity: 0, scaleY: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2, ease: 'easeOut' }}
                style={{ transformOrigin: 'bottom' }}
                className="flex flex-col items-stretch"
              >
                <div
                  className="stat-bar flex flex-col justify-start"
                  style={{
                    height: `clamp(8rem, ${heightPercent * 0.25}vw, ${heightPercent * 3.5}px)`,
                    minHeight: `${heightPercent * 2.8}px`,
                  }}
                >
                  <span className="text-3xl md:text-5xl lg:text-6xl font-black text-site-black/80">
                    <AnimatedCounter target={stat.percentage} isVisible={isVisible} />%
                  </span>
                </div>
                <p className="mt-4 text-sm md:text-base lg:text-lg font-bold text-site-text-light leading-snug">
                  {stat.label}{' '}
                  <span className="text-site-red">{stat.highlight}</span>
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default StatisticsSection;
