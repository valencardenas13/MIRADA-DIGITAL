import { useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import styles from './BeforeAfter.module.css';
import Reveal from './Reveal';
import { INSTAGRAM_URL } from '../content';
import { IconCheck, IconSwap, IconX } from './Icons';

const BEFORE = [
  'Posteás cuando te acordás',
  'Boosteás publicaciones sin saber qué volvió',
  'Los mensajes quedan sin responder',
  'No sabés de dónde vienen tus clientes',
];

const AFTER = [
  'Calendario de contenido pensado para vender',
  'Campañas con objetivo y presupuesto claro',
  'Cada consulta tiene seguimiento',
  'Medís qué funciona con Pixel y Tag Manager',
];

const LIST = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const ROW = { hidden: { opacity: 0, x: -10 }, show: { opacity: 1, x: 0 } };
const ROW_REDUCED = { hidden: { opacity: 0 }, show: { opacity: 1 } };

export default function BeforeAfter() {
  const [after, setAfter] = useState(true);
  const reduced = useReducedMotion();
  const items = after ? AFTER : BEFORE;

  return (
    <section className="section" id="antes-despues">
      <div className="container">
        <Reveal className="section-head">
          <div className="badge"><IconSwap /></div>
          <h2>Tu negocio en redes: antes y después</h2>
          <p>Menos improvisación, más clientes.</p>
        </Reveal>

        <Reveal className={styles.card}>
          <div className={styles.toggle} role="group" aria-label="Comparar">
            <button type="button" aria-pressed={!after} className={!after ? styles.active : ''} onClick={() => setAfter(false)}>
              Antes
            </button>
            <button type="button" aria-pressed={after} className={after ? styles.active : ''} onClick={() => setAfter(true)}>
              Con Mirada
            </button>
          </div>

          <h3 className={styles.title}>{after ? 'Menos vueltas, más ventas' : 'Mucho esfuerzo, poco resultado'}</h3>

          <AnimatePresence mode="wait">
            <motion.ul
              key={after ? 'after' : 'before'}
              className={styles.list}
              variants={LIST}
              initial="hidden"
              animate="show"
              exit="hidden"
            >
              {items.map((text) => (
                <motion.li key={text} variants={reduced ? ROW_REDUCED : ROW}>
                  <span>{text}</span>
                  <span className={after ? styles.yes : styles.no}>{after ? <IconCheck /> : <IconX />}</span>
                </motion.li>
              ))}
            </motion.ul>
          </AnimatePresence>

          <a className="btn btn-cyan btn-block" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Quiero el después
          </a>
        </Reveal>
      </div>
    </section>
  );
}
