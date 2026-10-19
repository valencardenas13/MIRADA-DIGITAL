import { motion, useReducedMotion } from 'motion/react';
import styles from './Diferenciales.module.css';

const CARDS = [
  {
    className: styles.cardAccent,
    title: 'Hablás con quien hace el trabajo',
    text: 'Sin cuentas comerciales en el medio ni cadena de aprobaciones. La persona que arma tu campaña es la misma que te responde el WhatsApp.',
    span: styles.wide,
  },
  {
    className: styles.cardNavy,
    title: 'Criterio de agencia grande',
    text: 'El equipo viene de manejar presupuestos y marcas a escala. Ese mismo estándar, aplicado a un comercio de barrio.',
    span: '',
  },
  {
    className: styles.cardCream,
    title: 'Sin contratos atados',
    text: 'Trabajamos mes a mes. Si no estás conforme, te vas cuando quieras — nos quedamos porque funciona, no porque firmaste algo.',
    span: '',
  },
  {
    className: styles.cardOutline,
    title: 'Zona Oeste, de cerca',
    text: 'Castelar y alrededores. Conocemos el comercio local porque caminamos la zona, no porque lo leímos en un informe.',
    span: styles.wide,
  },
];

const CONTAINER_MOTION = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const CONTAINER_REDUCED = { hidden: {}, show: { transition: { staggerChildren: 0 } } };

const cardVariant = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 140, damping: 20 } },
};

export default function Diferenciales() {
  const prefersReducedMotion = useReducedMotion();
  const container = prefersReducedMotion ? CONTAINER_REDUCED : CONTAINER_MOTION;

  return (
    <section id="por-que-mirada">
      <div className="container">
        <div className={styles.sectionHead}>
          <div className="eyebrow">Por qué Mirada</div>
          <h2>No somos la agencia más grande. Somos la que te atiende.</h2>
        </div>

        <motion.div
          className={styles.grid}
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.15 }}
        >
          {CARDS.map((card) => (
            <motion.div key={card.title} className={`${styles.card} ${card.className} ${card.span}`} variants={cardVariant}>
              <h3>{card.title}</h3>
              <p>{card.text}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
