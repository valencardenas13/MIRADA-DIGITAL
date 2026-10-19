import styles from './Footer.module.css';
import { INSTAGRAM_HANDLE, INSTAGRAM_URL } from '../content';

const YEAR = new Date().getFullYear();

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.top}`}>
        <div className={styles.cols}>
          <div className={styles.brandCol}>
            <span className={styles.wordmark}>Mirada Digital</span>
            <p>Agencia de marketing digital. Buenos Aires, Argentina.</p>
          </div>
          <div>
            <h4>Servicios</h4>
            <ul>
              <li><a href="#canales">Redes sociales</a></li>
              <li><a href="#canales">Meta & Google Ads</a></li>
              <li><a href="#canales">Web y tracking</a></li>
            </ul>
          </div>
          <div>
            <h4>Agencia</h4>
            <ul>
              <li><a href="#antes-despues">Por qué Mirada</a></li>
              <li><a href="#pasos">Cómo trabajamos</a></li>
              <li><a href="#faq">Preguntas frecuentes</a></li>
            </ul>
          </div>
          <div>
            <h4>Contacto</h4>
            <ul>
              <li>
                <a href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">{INSTAGRAM_HANDLE}</a>
              </li>
            </ul>
          </div>
        </div>

        <div className={styles.promo}>
          <span className={styles.promoMark} aria-hidden="true">M</span>
          <p>
            Vendé
            <br />
            más.
          </p>
        </div>
      </div>

      <div className={`container ${styles.legal}`}>
        <span>© {YEAR} Mirada Digital</span>
      </div>

      <div className={styles.bar}>
        <a className="btn btn-navy" href={INSTAGRAM_URL} target="_blank" rel="noopener noreferrer">
          Escribinos por Instagram
        </a>
      </div>
    </footer>
  );
}
