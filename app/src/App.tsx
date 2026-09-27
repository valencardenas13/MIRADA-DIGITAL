import ScrollProgress from './components/ScrollProgress';
import Nav from './components/Nav';
import Hero from './components/Hero';
import Banner from './components/Banner';
import Nosotros from './components/Nosotros';
import Services from './components/Services';
import Steps from './components/Steps';
import FinalCta from './components/FinalCta';
import Footer from './components/Footer';

export default function App() {
  return (
    <>
      <ScrollProgress />
      <Nav />
      <main>
        <Hero />
        <Banner />
        <Nosotros />
        <Services />
        <Steps />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
