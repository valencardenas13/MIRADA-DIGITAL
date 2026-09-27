import { motion, useReducedMotion } from 'motion/react';
import styles from './Services.module.css';
import ServiceCard from './ServiceCard';

const SERVICES = [
  { title: 'Meta Ads', description: 'Campañas de Instagram y Facebook armadas para vender, no para juntar likes.' },
  { title: 'Google Ads', description: 'Que te encuentren justo cuando te están buscando.' },
  { title: 'Redes sociales', description: 'Contenido y estrategia pensados para tu negocio, no una plantilla genérica.' },
  { title: 'Desarrollo web', description: 'Sitios en WordPress o Tienda Nube que convierten visitas en clientes.' },
  { title: 'Tracking', description: 'Meta Pixel y Google Tag Manager, para saber qué funciona de verdad.' },
  { title: 'Retargeting', description: 'Le volvemos a hablar a quien ya te vio, en el momento justo.' },
];

const CONTAINER_MOTION = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const CONTAINER_REDUCED = {
  hidden: {},
  show: { transition: { staggerChildren: 0 } },
};

export default function Services() {
  const prefersReducedMotion = useReducedMotion();
  const container = prefersReducedMotion ? CONTAINER_REDUCED : CONTAINER_MOTION;

  return (
    <section id="servicios">
      <div className="container">
        <div className={styles.sectionHead}>
          <div>
            <div className="eyebrow">Qué hacemos</div>
            <h2>Todo lo que necesitás. Nada que no.</h2>
          </div>
        </div>

        <motion.div
          className={styles.list}
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.1 }}
        >
          {SERVICES.map((s, i) => (
            <ServiceCard key={s.title} index={String(i + 1).padStart(2, '0')} title={s.title} description={s.description} />
          ))}
        </motion.div>
      </div>
    </section>
  );
}
