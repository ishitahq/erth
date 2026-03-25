import './App.css'
import Header from './components/Header/Header'
import HeroSection from './components/HeroSection/HeroSection'
import StatisticsSection from './components/StatisticsSection/StatisticsSection'
import SolutionSection from './components/SolutionSection/SolutionSection'
import PlasticTypesSection from './components/FoodPyramid/FoodPyramid'
import DeliverablesSection from './components/ResourcesSection/ResourcesSection'
import FAQSection from './components/FAQSection/FAQSection'
import Footer from './components/Footer/Footer'

function App() {
  return (
    <div className="min-h-screen bg-site-black">
      <Header />
      <main>
        <HeroSection />
        <StatisticsSection />
        <SolutionSection />
        <PlasticTypesSection />
        <DeliverablesSection />
        <FAQSection />
      </main>
      <Footer />
    </div>
  )
}

export default App
