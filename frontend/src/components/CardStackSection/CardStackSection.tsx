import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import type { MotionValue } from 'framer-motion';

interface CardData {
  id: number;
  bg: string;
  dark: boolean;
  rotate: number;
  zIndex: number;
  scrollStart: number;
  scrollEnd: number;
  lines: string[];
  subLine?: string;
}

const cardsConfig: CardData[] = [
  {
    id: 1,
    bg: '#f2efea',
    dark: false,
    rotate: -7,
    zIndex: 10,
    scrollStart: 0.05,
    scrollEnd: 0.32,
    lines: ['AI-Powered', 'Plastic', 'Waste', 'Classification.'],
    subLine: 'For Sustainable Recycling',
  },
  {
    id: 2,
    bg: '#1a1a1a',
    dark: true,
    rotate: -2,
    zIndex: 20,
    scrollStart: 0.35,
    scrollEnd: 0.62,
    lines: ['AI-Powered', 'Plastic', 'Waste', 'Classification.'],
  },
  {
    id: 3,
    bg: '#1a4a2e',
    dark: true,
    rotate: 4,
    zIndex: 30,
    scrollStart: 0.65,
    scrollEnd: 0.88,
    lines: ['Classify.', 'Recycle.', 'Sustain.'],
  },
];

const LogoBadge = ({ dark }: { dark: boolean }) => (
  <div
    className={`flex items-center gap-2 ${dark ? 'opacity-60' : 'opacity-50'}`}
  >
    <div
      className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-base ${
        dark ? 'border-white/70 text-white' : 'border-black/50 text-black'
      }`}
    >
      ♻
    </div>
    <div
      className={`border-l pl-2 ${
        dark ? 'border-white/50 text-white' : 'border-black/40 text-black'
      }`}
    >
      <p className="text-[9px] font-black tracking-[0.2em] uppercase leading-none">
        KABO
      </p>
      <p className="text-[9px] font-black tracking-[0.2em] uppercase leading-none mt-0.5">
        AI
      </p>
    </div>
  </div>
);

const Card = ({
  card,
  scrollYProgress,
}: {
  card: CardData;
  scrollYProgress: MotionValue<number>;
}) => {
  const x = useTransform(
    scrollYProgress,
    [card.scrollStart, card.scrollEnd],
    ['110%', '0%']
  );

  return (
    <motion.div
      style={{
        x,
        rotate: card.rotate,
        zIndex: card.zIndex,
        backgroundColor: card.bg,
        position: 'absolute',
        inset: 0,
      }}
      className="rounded-[2.5rem] shadow-2xl p-8 md:p-10 flex flex-col"
    >
      {/* Top: badge */}
      <div className="flex justify-end">
        <LogoBadge dark={card.dark} />
      </div>

      {/* Main text */}
      <div className="mt-4 flex-1">
        {card.lines.map((line, i) => (
          <p
            key={i}
            className={`font-black leading-[1.0] tracking-tight ${
              card.dark ? 'text-white' : 'text-site-text-dark'
            }`}
            style={{ fontSize: 'clamp(1.9rem, 7.5vw, 3.4rem)' }}
          >
            {line}
          </p>
        ))}
        {card.subLine && (
          <p
            className={`mt-3 font-semibold ${
              card.dark ? 'text-white/45' : 'text-black/38'
            }`}
            style={{ fontSize: 'clamp(0.9rem, 2.8vw, 1.35rem)' }}
          >
            {card.subLine}
          </p>
        )}
      </div>

      {/* Bottom bar */}
      <div
        className={`flex justify-between text-[10px] tracking-widest uppercase font-medium mt-4 ${
          card.dark ? 'text-white/30' : 'text-black/25'
        }`}
      >
        <span>kabo</span>
        <span>2025–2030</span>
      </div>
    </motion.div>
  );
};

export const CardStackSection = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section
      id="features"
      ref={containerRef}
      className="relative"
      style={{ height: '300vh' }}
    >
      <div
        className="sticky top-0 h-screen overflow-hidden flex items-center justify-center px-4"
        style={{ backgroundColor: '#ede9e0' }}
      >
        {/* Subtle section label */}
        <p
          className="absolute top-4 sm:top-8 left-1/2 -translate-x-1/2 text-[10px] sm:text-[11px] font-semibold tracking-[0.25em] uppercase text-black/30"
        >
          Key Features
        </p>

        {/* Card stack container */}
        <div
          className="relative"
          style={{
            width: 'min(350px, 90vw)',
            aspectRatio: '3 / 4',
          }}
        >
          {cardsConfig.map((card) => (
            <Card
              key={card.id}
              card={card}
              scrollYProgress={scrollYProgress}
            />
          ))}
        </div>

        {/* Scroll hint — fades out once first card has arrived */}
        <motion.p
          style={{
            opacity: useTransform(scrollYProgress, [0, 0.08], [1, 0]),
          }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-[11px] font-medium tracking-[0.2em] uppercase text-black/35 flex items-center gap-2"
        >
          <span>Scroll to explore</span>
          <motion.span
            animate={{ y: [0, 4, 0] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
          >
            ↓
          </motion.span>
        </motion.p>
      </div>
    </section>
  );
};

export default CardStackSection;
