import { useRef } from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'motion/react';
import styles from './Banner.module.css';
import officeBanner from '../assets/office-banner.jpg';

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
        initial={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, scale: 1.05 }}
        whileInView={prefersReducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}
