import { useState, useEffect } from 'react';

const sections = [
  { id: 'hero', label: 'Home' },
  { id: 'statistics', label: 'The Problem' },
  { id: 'solution', label: 'The Solution' },
  { id: 'plastic-types', label: 'Plastic Types' },
  { id: 'deliverables', label: 'Deliverables' },
  { id: 'faq', label: 'FAQs' },
];

export const Header = () => {
  const [activeSection, setActiveSection] = useState('hero');
  const [showNav, setShowNav] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowNav(window.scrollY > 200);

      const sectionElements = sections.map(s => ({
        id: s.id,
        el: document.getElementById(s.id),
      }));

      for (let i = sectionElements.length - 1; i >= 0; i--) {
        const el = sectionElements[i].el;
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= window.innerHeight / 3) {
            setActiveSection(sectionElements[i].id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      {/* Top Banner */}
      <div className="gov-banner">
        <span className="mr-2">♻️</span>
        AI-POWERED PLASTIC WASTE CLASSIFICATION SYSTEM
      </div>

      {/* Floating Nav Pill */}
      <nav
        className={`nav-pill transition-all duration-500 ${
          showNav ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4 pointer-events-none'
        }`}
      >
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => scrollToSection(section.id)}
            className="flex items-center gap-1.5 group"
            title={section.label}
          >
            <div
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                activeSection === section.id
                  ? 'bg-emerald-400 scale-125'
                  : 'bg-gray-500 group-hover:bg-gray-300'
              }`}
            />
            {activeSection === section.id && (
              <span className="text-xs font-bold text-site-text-light whitespace-nowrap">
                {section.label}
              </span>
            )}
          </button>
        ))}
      </nav>
    </>
  );
};

export default Header;
