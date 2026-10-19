import styles from './Steps.module.css';
import Reveal from './Reveal';
import { WHATSAPP_URL } from '../content';
import { IconEye, IconRocket } from './Icons';

export default function Steps() {
  return (
    <section className="section" id="pasos">
      <div className="container">
        <Reveal className="section-head">
          <div className="badge"><IconRocket /></div>
          <h2>Arrancamos en 3 pasos simples</h2>
          <p>Sin vueltas ni contratos largos. Trato directo con quien hace el trabajo, siempre.</p>
        </Reveal>

        <div className={styles.grid}>
          <Reveal className={styles.step}>
            <div className={`${styles.visual} ${styles.v1}`}>
              <span className={styles.fakeBtn}>Escribinos</span>
            </div>
            <h3>Paso 1: Nos conocemos</h3>
            <p>Hablamos por Instagram o WhatsApp. Vos contás cómo es tu negocio hoy.</p>
          </Reveal>

          <Reveal className={styles.step} delay={0.08}>
            <div className={`${styles.visual} ${styles.v2}`}>
              <span className={styles.mark}><IconEye /></span>
            </div>
            <h3>Paso 2: Armamos el plan</h3>
            <p>Definimos qué tiene sentido para vos: redes, publicidad, web, o las tres cosas.</p>
          </Reveal>

          <Reveal className={styles.step} delay={0.16}>
            <div className={`${styles.visual} ${styles.v3}`}>
              <span className={styles.msg}>¿Cómo vienen las campañas?</span>
              <span className={`${styles.msg} ${styles.msgUs}`}>Te paso el reporte del mes.</span>
            </div>
            <h3>Paso 3: Ejecutamos y ajustamos</h3>
            <p>Lanzamos, medimos y mejoramos todos los meses, con reportes claros.</p>
          </Reveal>
        </div>

        <div className={styles.ctas}>
          <a className="btn btn-cyan" href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer">
            Empezar ahora
          </a>
          <a className="btn btn-outline" href="#faq">
            Tengo dudas
          </a>
        </div>
      </div>
    </section>
  );
}
