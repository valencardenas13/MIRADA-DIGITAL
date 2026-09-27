import { motion, useReducedMotion } from 'motion/react';
import styles from './Services.module.css';

interface Props {
  index: string;
  title: string;
  description: string;
}

const rowVariant = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 120, damping: 20 } },
};

export default function ServiceCard({ index, title, description }: Props) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className={styles.row}
      variants={rowVariant}
      whileHover={prefersReducedMotion ? undefined : { x: 12 }}
      transition={{ type: 'spring', stiffness: 300, damping: 24 }}
    >
      <span className={styles.num}>{index}</span>
      <div className={styles.rowMain}>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <span className={styles.arrow}>↗</span>
    </motion.div>
  );
}
