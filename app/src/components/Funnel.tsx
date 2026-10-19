import styles from './Funnel.module.css';
import Reveal from './Reveal';
import { WHATSAPP_URL } from '../content';
import { IconChart } from './Icons';

const STAGES = [
  { title: 'Te descubren', text: 'Un anuncio o un posteo llega a la gente correcta de tu zona.' },
  { title: 'Te escriben', text: 'Llegan consultas por Instagram o WhatsApp.' },
  { title: 'Les respondés', text: 'Mensajes y seguimiento ordenados para no perder ninguna.' },
  { title: 'Te compran', text: 'Y con retargeting, te vuelven a comprar.' },
];

export default function Funnel() {
  return (
    <section className={`section on-dark ${styles.block}`}>
      <div className="container">
        <Reveal className="section-head">
          <div className="badge"><IconChart /></div>
          <h2>De un posteo suelto a un sistema que vende</h2>
          <p>Armamos el recorrido completo, desde que alguien te ve por primera vez hasta que te compra.</p>
        </Reveal>

        <Reveal className={styles.stage}>
          <div className={styles.panel}>
            <h3>Así funciona</h3>
            <ol>
              {STAGES.map((s, i) => (
                <li key={s.title}>
                  <span className={styles.num}>{i + 1}</span>
                  <div>
                    <strong>{s.title}</strong>
                    <span>{s.text}</span>
                  </div>
                </li>
              ))}
            </ol>
            <a className="btn btn-navy btn-block" href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer">
              Armemos el tuyo
            </a>
          </div>

          <div className={styles.phone} aria-hidden="true">
            <div className={styles.phoneTop}>
              <span className={styles.avatar} />
              <span>tu_negocio</span>
            </div>
            <div className={styles.thread}>
              <div className={styles.them}>Hola, vi la publicidad. ¿Cuánto sale?</div>
              <div className={styles.us}>¡Hola! Te paso la lista de precios y las promos de esta semana.</div>
              <div className={styles.them}>Genial, ¿puedo pasar mañana?</div>
              <div className={styles.us}>Claro, te esperamos de 10 a 19 hs.</div>
            </div>
          </div>

          <div className={styles.note}>
            Ejemplo ilustrativo de una conversación que nace de una campaña.
          </div>
        </Reveal>
      </div>
    </section>
  );
}
