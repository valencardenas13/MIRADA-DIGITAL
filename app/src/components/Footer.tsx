import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p>
        Mirada Digital — Buenos Aires, Argentina
        <br />
        <a href="https://instagram.com/somosmiradadigital" target="_blank" rel="noopener noreferrer">
          @somosmiradadigital
        </a>
      </p>
    </footer>
  );
}
