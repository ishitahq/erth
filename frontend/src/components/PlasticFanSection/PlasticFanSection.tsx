import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import type { MotionValue } from 'framer-motion';

const CARD_W = 270;
const CARD_H = 380;
const SHOW_W = 120;
const NUM_CARDS = 6;
const BASE_LEFT = 72;
const BUNDLE_CENTER = 520;
const BUNDLE_START = 0.78;
const BUNDLE_END = 0.88;

interface PlasticData {
  arrival: number;
  code: string;
  id: string;
  name: string;
  fullName: string;
  info: string;
  bg: string;
  dark: boolean;
  rotate: number;
  scrollStart: number;
  scrollEnd: number;
}

const plastics: PlasticData[] = [
  {
    arrival: 0,
    code: '#1',
    id: 'PET',
    name: 'PET',
    fullName: 'Polyethylene Terephthalate',
    info: 'Clear water bottles, soda bottles, food containers, polyester fabric.',
    bg: '#f2efea',
    dark: false,
    rotate: -5,
    scrollStart: 0.12,
    scrollEnd: 0.20,
  },
  {
    arrival: 1,
    code: '#2',
    id: 'HDPE',
    name: 'HDPE',
    fullName: 'High-Density Polyethylene',
    info: 'Milk jugs, detergent bottles, shampoo bottles, outdoor furniture.',
    bg: '#1a1a1a',
    dark: true,
    rotate: 3,
    scrollStart: 0.22,
    scrollEnd: 0.30,
  },
  {
    arrival: 2,
    code: '#3',
    id: 'LDPE',
    name: 'LDPE',
    fullName: 'Low-Density Polyethylene',
    info: 'Plastic bags, squeezable bottles, bread bags, cling wrap.',
    bg: '#1a4a2e',
    dark: true,
    rotate: -8,
    scrollStart: 0.32,
    scrollEnd: 0.40,
  },
  {
    arrival: 3,
    code: '#4',
    id: 'PP',
    name: 'PP',
    fullName: 'Polypropylene',
    info: 'Yogurt containers, bottle caps, straws, car parts, syringes.',
    bg: '#f2efea',
    dark: false,
    rotate: 6,
    scrollStart: 0.42,
    scrollEnd: 0.50,
  },
  {
    arrival: 4,
    code: '#5',
    id: 'PS',
    name: 'PS',
    fullName: 'Polystyrene',
    info: 'Foam cups, disposable cutlery, packing peanuts, CD cases.',
    bg: '#1a1a1a',
    dark: true,
    rotate: -3,
    scrollStart: 0.52,
    scrollEnd: 0.60,
  },
  {
    arrival: 5,
    code: '#6',
    id: 'PVC',
    name: 'PVC',
    fullName: 'Polyvinyl Chloride',
    info: 'Pipes, window frames, flooring, medical equipment tubing.',
    bg: '#1a4a2e',
    dark: true,
    rotate: 7,
    scrollStart: 0.62,
    scrollEnd: 0.70,
  },
];

const LogoBadge = ({ dark }: { dark: boolean }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      opacity: dark ? 0.6 : 0.5,
    }}
  >
    <div
      style={{
        width: 26,
        height: 26,
        borderRadius: '50%',
        border: `2px solid ${dark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 11,
        color: dark ? 'white' : 'black',
      }}
    >
      ♻
    </div>
    <div
      style={{
        borderLeft: `1.5px solid ${dark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)'}`,
        paddingLeft: 6,
      }}
    >
      <p
        style={{
          fontSize: 8,
          fontWeight: 900,
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          lineHeight: 1,
          color: dark ? 'white' : 'black',
          margin: 0,
        }}
      >
        KABO
      </p>
      <p
        style={{
          fontSize: 8,
          fontWeight: 900,
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          lineHeight: 1,
          color: dark ? 'white' : 'black',
          margin: '2px 0 0',
        }}
      >
        AI
      </p>
    </div>
  </div>
);

const FanCard = ({
  plastic,
  scrollYProgress,
}: {
  plastic: PlasticData;
  scrollYProgress: MotionValue<number>;
}) => {
  const finalLeft = BASE_LEFT + (NUM_CARDS - 1 - plastic.arrival) * SHOW_W;
  const bundleX = BUNDLE_CENTER - finalLeft;
  const zIndex = plastic.arrival + 1;

  const x = useTransform(
    scrollYProgress,
    [plastic.scrollStart, plastic.scrollEnd, BUNDLE_START, BUNDLE_END],
    [2000, 0, 0, bundleX]
  );

  const textLight = plastic.dark ? 'rgba(255,255,255,1)' : '#1a1a1a';
  const textMuted = plastic.dark ? 'rgba(255,255,255,0.52)' : 'rgba(0,0,0,0.45)';
  const textFaint = plastic.dark ? 'rgba(255,255,255,0.28)' : 'rgba(0,0,0,0.22)';

  return (
    <motion.div
      style={{
        position: 'absolute',
        left: finalLeft,
        top: `calc(65% - ${CARD_H / 2}px)`,
        width: CARD_W,
        height: CARD_H,
        x,
        rotate: plastic.rotate,
        zIndex,
        backgroundColor: plastic.bg,
        borderRadius: '2rem',
        boxShadow: '0 16px 56px rgba(0,0,0,0.26)',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Badge top-right */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <LogoBadge dark={plastic.dark} />
      </div>

      {/* Plastic code */}
      <p
        style={{
          marginTop: 12,
          fontSize: 12,
          fontWeight: 800,
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: textMuted,
          lineHeight: 1,
        }}
      >
        {plastic.code}
      </p>

      {/* Main name */}
      <p
        style={{
          marginTop: 6,
          fontSize: 56,
          fontWeight: 900,
          lineHeight: 1,
          letterSpacing: '-0.03em',
          color: textLight,
        }}
      >
        {plastic.name}
      </p>

      {/* Full name */}
      <p
        style={{
          marginTop: 8,
          fontSize: 13,
          fontWeight: 800,
          lineHeight: 1.35,
          color: textLight,
          flex: '0 0 auto',
        }}
      >
        {plastic.fullName}
      </p>

      {/* Info */}
      <p
        style={{
          marginTop: 8,
          fontSize: 12,
          lineHeight: 1.55,
          color: textMuted,
          flex: 1,
        }}
      >
        {plastic.info}
      </p>

      {/* Bottom bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 12,
          fontSize: 9,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          fontWeight: 600,
          color: textFaint,
        }}
      >
        <span>kaboai.io</span>
        <span>Recyclable</span>
      </div>
    </motion.div>
  );
};

export const PlasticFanSection = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section
      id="plastic-types"
      ref={containerRef}
      style={{ height: '400vh', position: 'relative' }}
    >
      <motion.div
        style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          overflow: 'hidden',
          backgroundColor: '#ede9e0',
          scale: useTransform(scrollYProgress, [0, 0.10], [0.95, 1]),
          borderRadius: useTransform(scrollYProgress, [0, 0.10], [24, 0]),
        }}
      >
        {/* Heading block — top-left */}
        <div
          style={{
            position: 'absolute',
            top: 48,
            left: 64,
            zIndex: 100,
          }}
        >
          <p
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.28em',
              textTransform: 'uppercase',
              color: '#2e7d52',
              marginBottom: 10,
            }}
          >
            Classification Categories
          </p>
          <p
            style={{
              fontSize: 'clamp(2rem, 3.5vw, 3.2rem)',
              fontWeight: 900,
              lineHeight: 1.05,
              letterSpacing: '-0.03em',
              color: '#1a1a1a',
              maxWidth: 520,
            }}
          >
            Our AI reads<br />
            every plastic type.
          </p>
        </div>

        {/* Right-side stat text — fades in after last card arrives */}
        <motion.div
          style={{
            position: 'absolute',
            right: 52,
            top: '50%',
            width: 248,
            zIndex: 100,
            opacity: useTransform(scrollYProgress, [BUNDLE_END, BUNDLE_END + 0.05], [0, 1]),
            y: useTransform(scrollYProgress, [BUNDLE_END, BUNDLE_END + 0.05], [30, 0]),
            translateY: '-50%',
          }}
        >
          {/* Label */}
          <p
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.28em',
              textTransform: 'uppercase',
              color: '#2e7d52',
              marginBottom: 12,
            }}
          >
            Model Performance
          </p>

          {/* Big accuracy number */}
          <p
            style={{
              fontSize: 92,
              fontWeight: 900,
              lineHeight: 1,
              letterSpacing: '-0.04em',
              color: '#1a1a1a',
            }}
          >
            94.7<span style={{ fontSize: 44, letterSpacing: '-0.02em' }}>%</span>
          </p>
          <p
            style={{
              marginTop: 10,
              fontSize: 15,
              lineHeight: 1.6,
              color: 'rgba(0,0,0,0.52)',
              fontWeight: 500,
            }}
          >
            Classification accuracy across all 6 resin codes under real-world conditions.
          </p>

          {/* Divider */}
          <div style={{ marginTop: 20, height: 1.5, backgroundColor: 'rgba(0,0,0,0.12)', borderRadius: 2 }} />

          {/* Per-type breakdown */}
          <p
            style={{
              marginTop: 16,
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.22em',
              textTransform: 'uppercase',
              color: 'rgba(0,0,0,0.35)',
              marginBottom: 10,
            }}
          >
            Per-Type Accuracy
          </p>
          {([
            ['PET', '97%'],
            ['HDPE', '96%'],
            ['LDPE', '91%'],
            ['PP',   '95%'],
            ['PS',   '93%'],
            ['PVC',  '96%'],
          ] as [string, string][]).map(([type, acc]) => (
            <div
              key={type}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 7,
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 700, color: '#1a1a1a' }}>{type}</span>
              <div style={{ flex: 1, height: 1, backgroundColor: 'rgba(0,0,0,0.1)', margin: '0 10px' }} />
              <span style={{ fontSize: 13, fontWeight: 800, color: '#2e7d52' }}>{acc}</span>
            </div>
          ))}

          {/* Divider */}
          <div style={{ marginTop: 16, height: 1.5, backgroundColor: 'rgba(0,0,0,0.12)', borderRadius: 2 }} />

          {/* Tagline */}
          <p
            style={{
              marginTop: 16,
              fontSize: 14,
              lineHeight: 1.65,
              color: 'rgba(0,0,0,0.42)',
              fontWeight: 500,
            }}
          >
            Dirty, deformed, or mixed —
            <br />the model reads them all.
          </p>
        </motion.div>

        {/* Fan cards */}
        {plastics.map((p) => (
          <FanCard key={p.id} plastic={p} scrollYProgress={scrollYProgress} />
        ))}
      </motion.div>
    </section>
  );
};

export default PlasticFanSection;
