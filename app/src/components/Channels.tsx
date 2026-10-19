import styles from './Channels.module.css';
import Reveal from './Reveal';
import { INSTAGRAM_URL } from '../content';
import { IconArrow, IconInstagram, IconMeta, IconSearch } from './Icons';

const CHANNELS = [
  {
    icon: <IconInstagram />,
    title: 'Redes sociales',
    text: 'Contenido y estrategia para Instagram y Facebook, pensados para tu negocio, no una plantilla genérica.',
  },
  {
    icon: <IconMeta />,
    title: 'Meta & Google Ads',
    text: 'Campañas armadas para vender, con retargeting para volver a hablarle a quien ya te vio.',
  },
  {
    icon: <IconSearch />,
    title: 'Web y tracking',
    text: 'Sitios en WordPress o Tienda Nube, con Meta Pixel y Tag Manager para medir qué funciona.',
  },
];

export default function Channels() {
  return (
    <section className={styles.block} id="canales">
      <div className={`container ${styles.expand}`}>
        <Reveal className={styles.expandCopy}>
          <h2>Llevá tu negocio a todos lados</h2>
          <p>
            No alcanza con estar en redes. Armamos una presencia digital completa — contenido, anuncios y web — que
            trabaja todos los días para traerte clientes nuevos.
          </p>
          <a className="btn btn-navy" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Quiero empezar
          </a>
        </Reveal>

        <Reveal className={styles.expandMedia} delay={0.1}>
          <div className={`photo-slot ${styles.photo}`}>Foto vertical (cliente / producto / equipo)</div>
          <div className={`${styles.chip} ${styles.chipTop}`}>Nuevo mensaje: “¿Hacen envíos?”</div>
          <div className={`${styles.chip} ${styles.chipBottom}`}>Campaña activa en Instagram</div>
        </Reveal>
      </div>

      <div className="container">
        <Reveal className="section-head">
          <h2>Donde está tu cliente, estás vos</h2>
        </Reveal>
        <div className={styles.cards}>
          {CHANNELS.map((c, i) => (
            <Reveal key={c.title} className={styles.card} delay={i * 0.08}>
              <div className={styles.cardHead}>
                <span className={styles.cardIcon}>{c.icon}</span>
                <h3>{c.title}</h3>
              </div>
              <p>{c.text}</p>
              <a className={styles.more} href="#pasos">
                Cómo trabajamos <IconArrow />
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
