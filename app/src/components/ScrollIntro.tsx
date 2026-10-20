import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion, useScroll, useTransform } from 'motion/react';
import styles from './ScrollIntro.module.css';
import sceneDesktop from '../assets/intro-scene.webp';
import sceneMobile from '../assets/intro-scene-mobile.webp';
import screenImg from '../assets/intro-screen.webp';

// Laptop screen position inside each scene image, as fractions of the image size.
const SCENES = {
  desktop: { src: sceneDesktop, ratio: 1024 / 572, cx: 0.5215, cy: 0.4266, w: 0.168, h: 0.173 },
  mobile: { src: sceneMobile, ratio: 572 / 992, cx: 0.554, cy: 0.4304, w: 0.322, h: 0.109 },
};

const ramp = (v: number, from: number, to: number) => Math.min(1, Math.max(0, (v - from) / (to - from)));

type Layout ={ W: number; H: number; scale: number; dx: number; dy: number; mobile: boolean };

function computeLayout(): Layout {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const mobile = vw / vh < 0.8;
  const s = mobile ? SCENES.mobile : SCENES.desktop;
  const W = Math.max(vw, vh * s.ratio);
  const H = W / s.ratio;
  // On portrait screens fill only the width; filling the height too would blow the screen up past its resolution.
  const fill = vw / (s.w * W);
  const scale = (mobile ? fill : Math.max(fill, vh / (s.h * H))) * 1.05;
  return { W, H, scale, dx: (0.5 - s.cx) * W, dy: (0.5 - s.cy) * H, mobile };
}

export default function ScrollIntro() {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = useReducedMotion();
  const [layout, setLayout] = useState<Layout>(() => computeLayout());

  useEffect(() => {
    const onResize = () => setLayout(computeLayout());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const { scrollYProgress: p } = useScroll({ target: ref, offset: ['start start', 'end end'] });

  const zoomEase = useTransform(p, [0, 0.62], [0, 1], { clamp: true, ease: (t) => t * t * (3 - 2 * t) });
  const scale = useTransform(zoomEase, [0, 1], [1, layout.scale]);
  const x = useTransform(zoomEase, [0, 1], [0, layout.dx]);
  const y = useTransform(zoomEase, [0, 1], [0, layout.dy]);
  const screenScale = useTransform(p, [0.48, 0.9], [1.2, 1]);
  const copyY = useTransform(p, [0.8, 0.94], [24, 0]);
  // Opacity uses the function form on purpose: the range form gets hardware-accelerated
  // against the scroll timeline and ends up at the wrong values inside this pinned track.
  const screenOpacity = useTransform(p, (v) => ramp(v, 0.48, 0.64));
  const veil = useTransform(p, (v) => ramp(v, 0.72, 0.9));
  const copyOpacity = useTransform(p, (v) => ramp(v, 0.8, 0.94));
  const hint = useTransform(p, (v) => 1 - ramp(v, 0, 0.08));

  const scene = layout.mobile ? SCENES.mobile : SCENES.desktop;
  const origin = `${scene.cx * 100}% ${scene.cy * 100}%`;

  if (reduced) {
    return (
      <section className={styles.static} aria-label="Introducción">
        <img className={styles.staticImg} src={scene.src} alt="" />
        <div className={styles.staticShade} />
        <h2 className={styles.copyText}>Tu próximo cliente ya está mirando.</h2>
      </section>
    );
  }

  return (
    <section ref={ref} className={styles.track} aria-label="Introducción">
      <div className={styles.stage}>
        <motion.div
          className={styles.scene}
          style={{ width: layout.W, height: layout.H, scale, x, y, transformOrigin: origin }}
        >
          <img src={scene.src} alt="Vista en primera persona de una notebook en la mesa de un café" />
        </motion.div>

        <motion.img
          className={styles.screen}
          src={screenImg}
          alt=""
          style={{ opacity: screenOpacity, scale: screenScale }}
        />

        <motion.div className={styles.veil} style={{ opacity: veil }} />

        <motion.div className={styles.copy} style={{ opacity: copyOpacity, y: copyY }}>
          <span className={styles.eyebrow}>Mirada Digital</span>
          <h2 className={styles.copyText}>Tu próximo cliente ya está mirando.</h2>
        </motion.div>

        <motion.div className={styles.hint} style={{ opacity: hint }} aria-hidden="true">
          Scrolleá para entrar
          <span className={styles.hintLine} />
        </motion.div>
      </div>
    </section>
  );
}
