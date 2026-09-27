import { useRef } from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'motion/react';
import styles from './Banner.module.css';
import officeBanner from '../assets/office-banner.jpg';

const INITIAL_MOTION = { opacity: 0, scale: 1.05 };
const INITIAL_REDUCED = { opacity: 0 };
const IN_VIEW_MOTION = { opacity: 1, scale: 1 };
const IN_VIEW_REDUCED = { opacity: 1 };

export default function Banner() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const prefersReducedMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start end', 'end start'],
  });

  const y = useTransform(scrollYProgress, [0, 1], prefersReducedMotion ? ['0%', '0%'] : ['-9%', '9%']);

  return (
    <div className={styles.banner} ref={containerRef}>
      <motion.img
        className={styles.img}
        src={officeBanner}
        alt="Oficina de Mirada Digital"
        style={{ y }}
        initial={prefersReducedMotion ? INITIAL_REDUCED : INITIAL_MOTION}
        whileInView={prefersReducedMotion ? IN_VIEW_REDUCED : IN_VIEW_MOTION}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}
