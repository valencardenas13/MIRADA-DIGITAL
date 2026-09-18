import { motion, useScroll, useTransform, useSpring } from 'motion/react';
import styles from './Nav.module.css';
import logoLight from '../assets/logo-light.svg';

const INSTAGRAM_URL = 'https://instagram.com/somosmiradadigital';

export default function Nav() {
  const { scrollY } = useScroll();
  const rawHeight = useTransform(scrollY, [0, 80], [64, 44]);
  const height = useSpring(rawHeight, { stiffness: 300, damping: 30 });
  const rawPadding = useTransform(scrollY, [0, 80], [22, 14]);
  const paddingBlock = useSpring(rawPadding, { stiffness: 300, damping: 30 });

  return (
    <motion.nav className={styles.nav} style={{ height, paddingTop: paddingBlock, paddingBottom: paddingBlock }}>
      <div className={styles.navInner}>
        <div className={styles.brand}>
          <img className={styles.brandLogo} src={logoLight} alt="Mirada Digital" />
          <span className={styles.brandWordmark}>Mirada Digital</span>
        </div>
        <div className={styles.navLinks}>
          <a href="#servicios">Qué hacemos</a>
          <a href="#nosotros">Nosotros</a>
          <a href="#como-trabajamos">Cómo trabajamos</a>
          <a className={styles.navCta} href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Escribinos
          </a>
        </div>
      </div>
    </motion.nav>
  );
}
