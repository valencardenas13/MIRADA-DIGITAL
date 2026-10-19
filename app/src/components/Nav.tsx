import styles from './Nav.module.css';
import logo from '../assets/logo.png';
import { INSTAGRAM_URL } from '../content';

export default function Nav() {
  return (
    <header className={styles.nav}>
      <div className={styles.inner}>
        <a href="#top" className={styles.brand} aria-label="Mirada Digital, inicio">
          <img src={logo} alt="Mirada Digital" />
        </a>
        <nav className={styles.links} aria-label="Principal">
          <a href="#canales">Servicios</a>
          <a href="#antes-despues">Por qué Mirada</a>
          <a href="#pasos">Cómo trabajamos</a>
          <a href="#faq">Preguntas</a>
        </nav>
        <div className={styles.actions}>
          <a className={`btn btn-outline ${styles.small} ${styles.hideMobile}`} href="#faq">
            Dudas
          </a>
          <a className={`btn btn-cyan ${styles.small}`} href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
            Escribinos
          </a>
        </div>
      </div>
    </header>
  );
}
