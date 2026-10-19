import { motion, useReducedMotion } from 'motion/react';
import styles from './Hero.module.css';
import { INSTAGRAM_URL } from '../content';
import { IconInstagram, IconMeta, IconSearch, IconWhatsApp } from './Icons';

const CONTAINER = { hidden: {}, show: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } } };
const ITEM = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const } },
};
const ITEM_REDUCED = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.3 } } };
const BUBBLE = {
  hidden: { opacity: 0, y: 16, scale: 0.96 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring' as const, stiffness: 160, damping: 18 } },
};

export default function Hero() {
  const reduced = useReducedMotion();
  const item = reduced ? ITEM_REDUCED : ITEM;
  const bubble = reduced ? ITEM_REDUCED : BUBBLE;

  return (
    <section className={styles.hero} id="top">
      <div className={`photo-slot ${styles.bg}`} aria-hidden="true">
        <span className={styles.slotLabel}>Foto principal (persona / equipo trabajando)</span>
      </div>
      <div className={styles.shade} aria-hidden="true" />

      <motion.div className={`container ${styles.inner}`} variants={CONTAINER} initial="hidden" animate="show">
        <div className={styles.copy}>
          <motion.h1 variants={item}>Que cada posteo te traiga clientes</motion.h1>
          <motion.p variants={item} className={styles.lede}>
            Manejamos tus redes, tu publicidad en Meta y Google, y tu web — con el criterio de una marca grande,
            aplicado a tu negocio.
          </motion.p>
          <motion.div variants={item}>
            <a className="btn btn-cyan" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
              Escribinos por Instagram
            </a>
          </motion.div>
          <motion.ul variants={item} className={styles.platforms} aria-label="Canales que manejamos">
            <li><IconInstagram /> Instagram</li>
            <li><IconMeta /> Meta Ads</li>
            <li><IconSearch /> Google Ads</li>
            <li><IconWhatsApp /> WhatsApp</li>
          </motion.ul>
        </div>

        <div className={styles.chat} aria-hidden="true">
          <motion.div variants={bubble} className={`${styles.bubble} ${styles.them}`}>
            Hola! Vi el anuncio, ¿tienen turnos esta semana?
          </motion.div>
          <motion.div variants={bubble} className={`${styles.bubble} ${styles.us}`}>
            ¡Hola! Sí, te paso los horarios disponibles.
          </motion.div>
          <motion.div variants={bubble} className={styles.tag}>
            Consulta que llegó desde una campaña
          </motion.div>
        </div>
      </motion.div>

      <div className={styles.strip}>
        <div className={`container ${styles.stripInner}`}>
          <span><strong>Atención directa</strong> con quien hace el trabajo</span>
          <span><strong>Sin contratos atados</strong> — trabajamos mes a mes</span>
          <span><strong>Buenos Aires, Argentina</strong></span>
        </div>
      </div>
    </section>
  );
}
