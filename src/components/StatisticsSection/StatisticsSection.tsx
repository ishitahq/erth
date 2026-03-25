import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';
import { statisticsData } from '../../data/statistics';

const AnimatedCounter = ({ target, isVisible }: { target: number; isVisible: boolean }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isVisible) return;
    let startTime: number | null = null;
    const duration = 2.0;

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

  const barHeights = ['h-40 md:h-56', 'h-48 md:h-64', 'h-56 md:h-80'];

  return (
    <section id="statistics" className="section-dark section-padding">
      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 md:mb-20"
        >
          <p className="text-emerald-400 text-sm md:text-base uppercase tracking-widest mb-4 font-semibold">
            The Plastic Crisis
          </p>
          <h2 className="heading-section mb-6">
            The planet is drowning
            <br />
            <span className="text-site-text-muted">in plastic waste.</span>
          </h2>
        </motion.div>

        {/* Red Bar Stats with counters */}
        <div ref={ref} className="grid grid-cols-3 gap-4 md:gap-8 items-end mb-16 max-w-5xl mx-auto">
          {statisticsData.map((stat, index) => (
            <motion.div
              key={stat.id}
              initial={{ opacity: 0, scaleY: 0 }}
              animate={isVisible ? { opacity: 1, scaleY: 1 } : {}}
              transition={{ duration: 0.8, delay: index * 0.2, ease: 'easeOut' }}
              style={{ transformOrigin: 'bottom' }}
              className="flex flex-col items-stretch"
            >
              <div className={`stat-bar ${barHeights[index]} flex flex-col justify-start`}>
                <span className="text-3xl md:text-5xl lg:text-6xl font-black text-site-black/80">
                  <AnimatedCounter target={stat.percentage} isVisible={isVisible} />%
                </span>
              </div>
              <p className="mt-4 text-sm md:text-base lg:text-lg font-bold text-site-text-light leading-snug">
                {stat.label}{' '}
                <span className="text-site-red">{stat.highlight}</span>
              </p>
            </motion.div>
          ))}
        </div>

        {/* Bottom text */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="body-large text-center max-w-4xl mx-auto mt-16"
        >
          <span className="text-site-text-light">
            Manual plastic identification is slow, error-prone, and inconsistent.
          </span>{' '}
          <span className="text-site-text-muted">
            Misclassification contaminates recycling streams, reduces material value, and sends
            recyclable plastic to landfills.
          </span>
        </motion.p>
      </div>
    </section>
  );
};

export default StatisticsSection;
