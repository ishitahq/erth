import './App.css'
import Header from './components/Header/Header'
import HeroSection from './components/HeroSection/HeroSection'
import StatisticsSection from './components/StatisticsSection/StatisticsSection'
import ScrollRevealText from './components/ScrollRevealText/ScrollRevealText'
import PlasticFanSection from './components/PlasticFanSection/PlasticFanSection'
import DeliverablesSection from './components/ResourcesSection/ResourcesSection'
import FAQSection from './components/FAQSection/FAQSection'
import Footer from './components/Footer/Footer'
import SmoothCursor from './components/SmoothCursor/SmoothCursor'

function App() {
  return (
    <div className="min-h-screen bg-site-black cursor-none">
      <SmoothCursor />
      <Header />
      <main>
        <HeroSection />
        <StatisticsSection />
        <ScrollRevealText />
        <PlasticFanSection />
        <DeliverablesSection />
        <FAQSection />
      </main>
      <Footer />
    </div>
  )
}

export default App
