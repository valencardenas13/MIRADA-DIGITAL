import Reveal from './Reveal';
import { IconEye } from './Icons';

export default function Intro() {
  return (
    <section className="section">
      <Reveal className="container section-head">
        <div className="badge"><IconEye /></div>
        <h2>Hacé crecer lo que ya funciona en tu negocio</h2>
        <p>Estrategia, contenido y publicidad trabajando juntos, para que te encuentren, te elijan y te vuelvan a comprar.</p>
      </Reveal>
    </section>
  );
}
