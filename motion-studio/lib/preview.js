// Reproductor para previsualizar un film en el navegador. En modo render no hace nada:
// render.mjs define window.__RENDER__ y llama a window.seek(t) frame por frame.
(function () {
  if (window.__RENDER__) return;

  window.addEventListener("load", () => {
    const film = window.FILM;
    const stage = document.getElementById("stage");

    // Escala el stage para que entre en la ventana.
    const fit = () => {
      const s = Math.min(innerWidth / film.width, innerHeight / film.height);
      stage.style.transformOrigin = "0 0";
      stage.style.transform = `translate(${(innerWidth - film.width * s) / 2}px, 0) scale(${s})`;
    };
    fit();
    addEventListener("resize", fit);

    const audio = new Audio("audio.wav");
    let playing = false;
    let t = 0;

    const loop = () => {
      if (!playing) return;
      t = audio.duration ? audio.currentTime : t + 1 / film.fps;
      if (t >= film.duration) { t = 0; audio.currentTime = 0; }
      window.seek(t);
      requestAnimationFrame(loop);
    };

    const toggle = () => {
      playing = !playing;
      if (playing) {
        audio.currentTime = t;
        audio.play().catch(() => {});
        requestAnimationFrame(loop);
      } else {
        audio.pause();
      }
    };

    addEventListener("click", toggle);
    addEventListener("keydown", (e) => {
      if (e.code === "Space") toggle();
      if (e.code === "ArrowRight" || e.code === "ArrowLeft") {
        t = Math.min(film.duration, Math.max(0, t + (e.code === "ArrowRight" ? 1 : -1) / film.fps * (e.shiftKey ? film.fps : 1)));
        audio.currentTime = t;
        window.seek(t);
      }
    });

    window.seek(0);
  });
})();
