import ScrollProgress from './components/ScrollProgress';
import Nav from './components/Nav';
import ScrollIntro from './components/ScrollIntro';
import Hero from './components/Hero';
import Intro from './components/Intro';
import Channels from './components/Channels';
import BeforeAfter from './components/BeforeAfter';
import Funnel from './components/Funnel';
import Steps from './components/Steps';
import Faq from './components/Faq';
import Footer from './components/Footer';

export default function App() {
  return (
    <>
      <ScrollProgress />
      <Nav />
      <main>
        <ScrollIntro />
        <Hero />
        <Intro />
        <Channels />
        <BeforeAfter />
        <Funnel />
        <Steps />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
