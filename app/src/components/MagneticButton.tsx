import { motion } from 'motion/react';
import { useMagnetic } from '../hooks/useMagnetic';
import type { ReactNode } from 'react';

interface Props {
  href: string;
  className: string;
  children: ReactNode;
  target?: string;
  rel?: string;
}

export default function MagneticButton({ href, className, children, target, rel }: Props) {
  const { ref, x, y, onMouseMove, onMouseLeave } = useMagnetic();

  return (
    <motion.a
      ref={ref as React.Ref<HTMLAnchorElement>}
      href={href}
      target={target}
      rel={rel}
      className={className}
      style={{ x, y }}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
    >
      {children}
    </motion.a>
  );
}
