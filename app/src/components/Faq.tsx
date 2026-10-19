import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import styles from './Faq.module.css';
import Reveal from './Reveal';
import { IconPlus, IconQuestion } from './Icons';

const FAQS = [
  {
    q: '¿Con qué tipo de negocios trabajan?',
    a: 'Con comercios y emprendimientos que quieren vender más usando redes y publicidad: locales a la calle, servicios profesionales, tiendas online y marcas que están arrancando.',
  },
  {
    q: '¿Tengo que firmar un contrato largo?',
    a: 'No. Trabajamos mes a mes. Si no estás conforme, podés dejar cuando quieras.',
  },
  {
    q: '¿El presupuesto de publicidad está incluido?',
    a: 'No: lo que se invierte en Meta o Google lo pagás directo a la plataforma, desde tu cuenta. Nosotros cobramos por la gestión, así siempre sabés cuánto va a anuncios.',
  },
  {
    q: '¿Con quién hablo en el día a día?',
    a: 'Directamente con la persona que trabaja tu cuenta. Sin intermediarios ni cadena de mando.',
  },
  {
    q: '¿Cómo sé si está funcionando?',
    a: 'Configuramos Meta Pixel y Google Tag Manager para medir consultas y ventas, y te pasamos un reporte claro todos los meses.',
  },
  {
    q: '¿Trabajan solo en Buenos Aires?',
    a: 'Estamos en Buenos Aires, Argentina, pero podemos trabajar con negocios de cualquier parte del país de forma remota.',
  },
];

export default function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className={`section on-dark ${styles.block}`} id="faq">
      <div className="container">
        <Reveal className="section-head">
          <div className="badge"><IconQuestion /></div>
          <h2>Preguntas frecuentes</h2>
        </Reveal>

        <div className={styles.list}>
          {FAQS.map((item, i) => {
            const isOpen = open === i;
            return (
              <div key={item.q} className={styles.item}>
                <button
                  type="button"
                  className={styles.q}
                  aria-expanded={isOpen}
                  aria-controls={`faq-${i}`}
                  onClick={() => setOpen(isOpen ? null : i)}
                >
                  <span>{item.q}</span>
                  <span className={`${styles.icon} ${isOpen ? styles.iconOpen : ''}`}><IconPlus /></span>
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      id={`faq-${i}`}
                      className={styles.a}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <p>{item.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
