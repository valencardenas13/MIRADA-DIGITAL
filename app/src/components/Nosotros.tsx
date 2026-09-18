import { motion, useReducedMotion } from 'motion/react';
import styles from './Nosotros.module.css';
import officeDesk from '../assets/office-desk.jpg';

export default function Nosotros() {
  const prefersReducedMotion = useReducedMotion();

  const imgVariants = prefersReducedMotion
    ? {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { duration: 0.5 } },
      }
    : {
        hidden: { clipPath: 'inset(0 0 0 100%)' },
        show: { clipPath: 'inset(0 0 0 0%)', transition: { duration: 0.9, ease: [0.65, 0, 0.35, 1] as const } },
      };

  const textVariants = prefersReducedMotion
    ? {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { duration: 0.5, delay: 0.15 } },
      }
    : {
        hidden: { opacity: 0, x: -24 },
        show: { opacity: 1, x: 0, transition: { type: 'spring' as const, stiffness: 110, damping: 22, delay: 0.25 } },
      };

  return (
    <section className="surface" id="nosotros">
      <div className="container">
        <div className={styles.grid}>
          <motion.div
            className={styles.text}
            variants={textVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.4 }}
          >
            <h2>
              Laburamos como en las <span className="accent-word">multinacionales</span>. Para negocios como el
              tuyo.
            </h2>
            <p className={styles.support}>
              El equipo viene de manejar campañas a escala en agencias y marcas grandes. Ese mismo criterio — no la
              improvisación de "subamos una foto y vemos qué pasa" — es el que aplicamos a cada cliente, sin importar
              el tamaño del negocio.
            </p>
          </motion.div>

          <motion.img
            className={styles.img}
            src={officeDesk}
            alt="Escritorio de trabajo de Mirada Digital"
            variants={imgVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.4 }}
          />
        </div>
      </div>
    </section>
  );
}
