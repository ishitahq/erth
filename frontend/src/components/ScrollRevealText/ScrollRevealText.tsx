import { useRef } from 'react';
import { useScroll, useTransform, motion } from 'framer-motion';

const TEXT = 'Millions of tons of plastic pollute our planet each year. Our AI identifies plastic in real time; turning waste into valuable, scalable recycling.'

const Word = ({
  word,
  index,
  totalWords,
  scrollYProgress,
}: {
  word: string;
  index: number;
  totalWords: number;
  scrollYProgress: ReturnType<typeof useScroll>['scrollYProgress'];
}) => {
  // Map each word to a slice of the 0.15 – 0.85 scroll range
  const start = 0.15 + (index / totalWords) * 0.7;
  const end = 0.15 + ((index + 1) / totalWords) * 0.7;

  const color = useTransform(
    scrollYProgress,
    [start, end],
    ['rgba(255,255,255,0.2)', 'rgba(255,255,255,1)']
  );

  return (
    <motion.span style={{ color, transition: 'color 0.05s ease' }}>
      {word}{' '}
    </motion.span>
  );
};

export const ScrollRevealText = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  const words = TEXT.split(' ');

  return (
    <div
      ref={containerRef}
      className="section-dark"
      style={{ height: '130vh', position: 'relative' }}
    >
      <div
        style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div className="section-container">
          <p
            style={{
              fontSize: 'clamp(1.2rem, 2.8vw, 2.2rem)',
              fontWeight: 800,
              lineHeight: 1.5,
              letterSpacing: '-0.02em',
              maxWidth: '900px',
              margin: '0 auto',
              textAlign: 'center',
            }}
          >
            {words.map((word, i) => (
              <Word
                key={`${word}-${i}`}
                word={word}
                index={i}
                totalWords={words.length}
                scrollYProgress={scrollYProgress}
              />
            ))}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScrollRevealText;
