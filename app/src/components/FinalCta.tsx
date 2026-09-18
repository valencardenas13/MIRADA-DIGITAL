import { motion, useReducedMotion } from 'motion/react';
import styles from './FinalCta.module.css';
import MagneticButton from './MagneticButton';

const INSTAGRAM_URL = 'https://instagram.com/somosmiradadigital';

export default function FinalCta() {
  const prefersReducedMotion = useReducedMotion();

  const h2Variant = prefersReducedMotion
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.5 } } }
    : {
        hidden: { opacity: 0, scale: 0.9 },
        show: { opacity: 1, scale: 1, transition: { type: 'spring' as const, stiffness: 200, damping: 12 } },
      };

  return (
    <section className={styles.section}>
      <div className="container">
        <motion.h2
          className={styles.h2}
          variants={h2Variant}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.6 }}
        >
          Empecemos.
        </motion.h2>
        <div className={styles.ctas}>
          <MagneticButton className="btn btn-primary" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Escribinos por Instagram
          </MagneticButton>
        </div>
      </div>
    </section>
  );
}
