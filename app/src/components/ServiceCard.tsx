import { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from 'motion/react';
import styles from './Services.module.css';

interface Props {
  title: string;
  description: string;
}

const TILT_MAX = 5;

const cardVariant = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 120, damping: 20 } },
};

export default function ServiceCard({ title, description }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const prefersReducedMotion = useReducedMotion();

  const rotateXValue = useMotionValue(0);
  const rotateYValue = useMotionValue(0);
  const rotateX = useSpring(rotateXValue, { stiffness: 200, damping: 20 });
  const rotateY = useSpring(rotateYValue, { stiffness: 200, damping: 20 });
  const scale = useSpring(1, { stiffness: 200, damping: 20 });
  const shadow = useTransform(
    scale,
    [1, 1.02],
    ['0 0px 0px rgba(0,0,0,0)', '0 18px 40px rgba(0,0,0,0.14)']
  );

  const handleMouseMove = (e: React.MouseEvent) => {
    if (prefersReducedMotion || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    rotateYValue.set(px * TILT_MAX * 2);
    rotateXValue.set(-py * TILT_MAX * 2);
  };

  const handleMouseEnter = () => {
    if (!prefersReducedMotion) scale.set(1.02);
  };

  const handleMouseLeave = () => {
    rotateXValue.set(0);
    rotateYValue.set(0);
    scale.set(1);
  };

  return (
    <motion.div
      ref={ref}
      className={styles.card}
      variants={cardVariant}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX: prefersReducedMotion ? 0 : rotateX,
        rotateY: prefersReducedMotion ? 0 : rotateY,
        scale: prefersReducedMotion ? 1 : scale,
        boxShadow: prefersReducedMotion ? undefined : shadow,
        perspective: 800,
      }}
    >
      <h3>{title}</h3>
      <p>{description}</p>
    </motion.div>
  );
}
