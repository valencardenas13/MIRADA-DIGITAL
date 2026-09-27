import { motion, useReducedMotion } from 'motion/react';
import styles from './Hero.module.css';
import MagneticButton from './MagneticButton';

const INSTAGRAM_URL = 'https://instagram.com/somosmiradadigital';
const HEADLINE = 'Dejá de boostear posteos.';

const spring = { type: 'spring' as const, stiffness: 120, damping: 20 };

export default function Hero() {
  const prefersReducedMotion = useReducedMotion();
  const words = HEADLINE.split(' ');

  const container = {
    hidden: {},
    show: {
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.09,
        delayChildren: 0.1,
      },
    },
  };

  const fadeUp = prefersReducedMotion
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.4 } } }
    : { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: spring } };

  const wordVariant = prefersReducedMotion
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.4 } } }
    : { hidden: { opacity: 0, y: 30 }, show: { opacity: 1, y: 0, transition: spring } };

  return (
    <section className={styles.hero}>
      <motion.div className="container" variants={container} initial="hidden" animate="show">
        <motion.div className="eyebrow" variants={fadeUp}>
          Mirada Digital · Agencia de Marketing Digital
        </motion.div>

        <motion.h1 className={styles.h1} variants={container}>
          {words.map((word, i) => (
            <motion.span key={i} className={styles.word} variants={wordVariant}>
              {word}
            </motion.span>
          ))}
        </motion.h1>

        <motion.p className={styles.lede} variants={fadeUp}>
          Manejamos tus redes y tu publicidad en Meta con la misma disciplina con la que se maneja una marca grande.
          Aplicada a tu negocio, en tu zona.
        </motion.p>

        <motion.div className={styles.ctas} variants={fadeUp}>
          <MagneticButton className="btn btn-primary" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Escribinos por Instagram
          </MagneticButton>
          <MagneticButton className="btn btn-secondary" href="#servicios">
            Ver qué hacemos ›
          </MagneticButton>
        </motion.div>
      </motion.div>
    </section>
  );
}
