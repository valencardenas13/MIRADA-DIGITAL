import { motion, useReducedMotion } from 'motion/react';
import styles from './Steps.module.css';

const STEPS = [
  { num: '01', title: 'Nos conocemos', text: 'Pasamos por tu local o hablamos por WhatsApp. Vos contás cómo es tu negocio hoy.' },
  { num: '02', title: 'Armamos el plan', text: 'Definimos qué tiene sentido para vos: redes, publicidad, web, o las tres cosas.' },
  { num: '03', title: 'Ejecutamos y ajustamos', text: 'Trato directo con quien hace el trabajo, siempre. Sin cadena de mando en el medio.' },
];

export default function Steps() {
  const prefersReducedMotion = useReducedMotion();

  const numVariant = prefersReducedMotion
    ? { hidden: { opacity: 0 }, show: { opacity: 1, transition: { duration: 0.4 } } }
    : {
        hidden: { opacity: 0, scale: 0.6 },
        show: { opacity: 1, scale: 1, transition: { type: 'spring' as const, stiffness: 260, damping: 18 } },
      };

  const textVariant = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <section id="como-trabajamos">
      <div className="container">
        <div className={styles.sectionHead}>
          <div className="eyebrow" style={{ textAlign: 'center' }}>
            Cómo trabajamos
          </div>
          <h2>Sin intermediarios. Sin vueltas.</h2>
        </div>

        <div className={styles.steps}>
          {STEPS.map((step, i) => (
            <div className={styles.step} key={step.num}>
              <motion.div
                className={styles.stepNum}
                variants={numVariant}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.6 }}
                transition={{ delay: i * 0.15 }}
              >
                {step.num}
              </motion.div>
              <motion.div
                variants={textVariant}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.6 }}
                transition={{ delay: i * 0.15 + 0.1 }}
              >
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </motion.div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
