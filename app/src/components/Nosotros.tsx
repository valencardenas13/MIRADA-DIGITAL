import { motion, useReducedMotion } from 'motion/react';
import styles from './Nosotros.module.css';
import officeDesk from '../assets/office-desk.jpg';

const CURTAIN_VARIANTS = {
  hidden: { scaleX: 1 },
  show: { scaleX: 0, transition: { duration: 0.8, ease: [0.65, 0, 0.35, 1] as const } },
};

const CURTAIN_VARIANTS_REDUCED = {
  hidden: { scaleX: 0 },
  show: { scaleX: 0 },
};

const TEXT_VARIANTS_MOTION = {
  hidden: { opacity: 0, x: -24 },
  show: { opacity: 1, x: 0, transition: { type: 'spring' as const, stiffness: 110, damping: 22, delay: 0.25 } },
};

const TEXT_VARIANTS_REDUCED = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.5, delay: 0.15 } },
};

export default function Nosotros() {
  const prefersReducedMotion = useReducedMotion();

  const curtainVariants = prefersReducedMotion ? CURTAIN_VARIANTS_REDUCED : CURTAIN_VARIANTS;
  const textVariants = prefersReducedMotion ? TEXT_VARIANTS_REDUCED : TEXT_VARIANTS_MOTION;

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

          <div className={styles.imgWrap}>
            <img className={styles.img} src={officeDesk} alt="Escritorio de trabajo de Mirada Digital" />
            <motion.div
              className={styles.curtain}
              variants={curtainVariants}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
