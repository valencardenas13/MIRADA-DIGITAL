import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'motion/react';

const VARIANTS = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const } },
};

const VARIANTS_REDUCED = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.3 } },
};

const VIEWPORT = { once: true, amount: 0.2 };

interface Props {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export default function Reveal({ children, className, delay = 0 }: Props) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      variants={reduced ? VARIANTS_REDUCED : VARIANTS}
      initial="hidden"
      whileInView="show"
      viewport={VIEWPORT}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  );
}
