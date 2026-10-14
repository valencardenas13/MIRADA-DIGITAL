// Render de films por seek(t). Ver CLAUDE.md para el contrato.
//
//   node render.mjs films/<nombre>              render completo -> out/<nombre>.mp4
//   node render.mjs films/<nombre> --sheet      hoja de contactos, un frame por beat
//   node render.mjs films/<nombre> --frame 3.2  un frame suelto
//   node render.mjs films/<nombre> --check      lint + chequeo de determinismo
//   --no-audio                                  render sin mezclar audio.wav

import { createHash } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import browser from "./lib/browser.js";

const args = process.argv.slice(2);
const filmDir = args.find((a) => !a.startsWith("--") && !/^[\d.]+$/.test(a));
if (!filmDir) {
  console.error("uso: node render.mjs films/<nombre> [--sheet | --frame <t> | --check] [--no-audio]");
  process.exit(1);
}
const flag = (name) => args.includes(`--${name}`);
const frameArg = flag("frame") ? Number(args[args.indexOf("--frame") + 1]) : null;

const name = path.basename(path.resolve(filmDir));
const outDir = path.resolve("out");
mkdirSync(outDir, { recursive: true });

// --- Lint del contrato de render ---

const BANNED = [
  [/Math\.random/, "Math.random (usar F.mulberry32 / F.hash)"],
  [/\bsetTimeout\b|\bsetInterval\b/, "setTimeout/setInterval"],
  [/requestAnimationFrame/, "requestAnimationFrame"],
  [/\bDate\.now\b|performance\.now/, "reloj del sistema (Date.now / performance.now)"],
  [/transition\s*:|\.transition\s*=/, "CSS transition"],
  [/animation\s*:|@keyframes|\.animate\s*\(/, "CSS/Web animation"],
];

function lint() {
  const problems = [];
  for (const file of readdirSync(filmDir)) {
    if (!/\.(html|js|css|mjs)$/.test(file) || file === "beats.js") continue;
    const lines = readFileSync(path.join(filmDir, file), "utf8").split("\n");
    lines.forEach((line, i) => {
      for (const [re, what] of BANNED) {
        if (re.test(line)) problems.push(`${file}:${i + 1}  ${what}`);
      }
    });
  }
  if (problems.length) {
    console.error("El film rompe el contrato de render:\n  " + problems.join("\n  "));
    process.exit(1);
  }
}

// --- Navegador ---

async function openFilm() {
  const b = await browser.launch();
  const page = await b.newPage();
  page.on("pageerror", (e) => console.error("error en el film:", e.message));
  await page.addInitScript(() => {
    window.__RENDER__ = true;
  });
  await page.goto(pathToFileURL(path.resolve(filmDir, "index.html")).href);
  const film = await page.evaluate(() => window.FILM);
  if (!film || typeof film.duration !== "number") throw new Error("index.html debe definir window.FILM");
  await page.setViewportSize({ width: film.width, height: film.height });
  await page.evaluate(async () => {
    await document.fonts.ready;
    if (window.ready) await window.ready;
  });
  const shoot = async (t, opts = {}) => {
    await page.evaluate((t) => window.seek(t), t);
    return page.screenshot({ type: "png", ...opts });
  };
  return { b, page, film, shoot };
}

const hash = (buf) => createHash("sha1").update(buf).digest("hex");

function readBeats() {
  const p = path.join(filmDir, "beats.json");
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null;
}

// --- Modos ---

async function check() {
  const { b, film, shoot } = await openFilm();
  const mid = Math.round((film.duration / 2) * film.fps) / film.fps;
  const end = (Math.round(film.duration * film.fps) - 1) / film.fps;
  const first = hash(await shoot(mid));
  await shoot(0);
  await shoot(end);
  await shoot(mid / 3);
  const again = hash(await shoot(mid));
  await b.close();
  if (first !== again) {
    console.error(`No es determinista: el frame t=${mid}s cambia según qué se renderizó antes.`);
    process.exit(1);
  }
  console.log(`ok: contrato respetado y frame t=${mid}s idéntico tras seeks desordenados`);
}

async function frame(t) {
  const { b, shoot } = await openFilm();
  const file = path.join(outDir, `${name}-${t.toFixed(2)}.png`);
  writeFileSync(file, await shoot(t));
  await b.close();
  console.log(file);
}

async function sheet() {
  const { b, page, film, shoot } = await openFilm();
  const data = readBeats();
  const bars = new Set((data?.bars || []).map((x) => x.toFixed(4)));
  let times = data?.beats?.length
    ? data.beats.filter((t) => t < film.duration)
    : Array.from({ length: Math.ceil(film.duration * 2) }, (_, i) => i * 0.5);
  if (!times.length || times[0] > 0.1) times = [0, ...times];

  const thumbs = [];
  for (const [i, t] of times.entries()) {
    const png = await shoot(t);
    thumbs.push({ t, i, bar: bars.has(t.toFixed(4)), src: "data:image/png;base64," + png.toString("base64") });
  }

  const cols = 8;
  const w = 270;
  const h = Math.round((w * film.height) / film.width);
  const html = `<!doctype html><meta charset="utf-8"><style>
    body{margin:0;background:#111;font:600 15px Inter,system-ui,sans-serif;color:#ddd;padding:16px}
    h1{font-size:18px;margin:0 0 12px}
    .g{display:grid;grid-template-columns:repeat(${cols},${w}px);gap:10px}
    figure{margin:0} img{width:${w}px;height:${h}px;display:block;border:2px solid #222}
    .bar img{border-color:#00d4ff} figcaption{padding:4px 2px}
  </style><h1>${name} · ${times.length} frames · ${data ? data.tempo.toFixed(1) + " BPM" : "sin beats.json (cada 0.5s)"}</h1>
  <div class="g">${thumbs
    .map((x) => `<figure class="${x.bar ? "bar" : ""}"><img src="${x.src}"><figcaption>${x.t === 0 && x.i === 0 && data ? "inicio" : "b" + x.i} · ${x.t.toFixed(2)}s${x.bar ? " · compás" : ""}</figcaption></figure>`)
    .join("")}</div>`;
  const sheetPage = await b.newPage({ viewport: { width: cols * (w + 10) + 32, height: 400 } });
  await sheetPage.setContent(html);
  const file = path.join(outDir, `${name}-sheet.png`);
  await sheetPage.screenshot({ path: file, fullPage: true });
  await b.close();
  console.log(`${file} (${times.length} frames)`);
}

function loudnorm(audio, duration, video, out) {
  const filter = "loudnorm=I=-14:TP=-1:LRA=11";
  const pass1 = spawnSync("ffmpeg", ["-hide_banner", "-i", audio, "-af", `${filter}:print_format=json`, "-f", "null", "-"], { encoding: "utf8" });
  const m = JSON.parse(pass1.stderr.slice(pass1.stderr.lastIndexOf("{")));
  const measured = `measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
  const pass2 = spawnSync(
    "ffmpeg",
    ["-hide_banner", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
     "-af", `${filter}:${measured}:print_format=json,aresample=48000,apad`,
     "-t", String(duration), "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out],
    { encoding: "utf8" },
  );
  if (pass2.status !== 0) throw new Error(pass2.stderr.slice(-2000));
  const r = JSON.parse(pass2.stderr.slice(pass2.stderr.lastIndexOf("{"), pass2.stderr.lastIndexOf("}") + 1));
  return { input: Number(m.input_i), output: Number(r.output_i), tp: Number(r.output_tp) };
}

async function full() {
  const { b, film, shoot } = await openFilm();
  const total = Math.round(film.duration * film.fps);
  const silent = path.join(outDir, `${name}.video.mp4`);
  const ff = spawn("ffmpeg", [
    "-hide_banner", "-loglevel", "error", "-y",
    "-f", "image2pipe", "-framerate", String(film.fps), "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", silent,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Promise((res, rej) => ff.on("close", (c) => (c === 0 ? res() : rej(new Error(`ffmpeg salió con ${c}`)))));

  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    const png = await shoot(i / film.fps);
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
    if (i % film.fps === 0) process.stdout.write(`\rframe ${i}/${total}`);
  }
  ff.stdin.end();
  await done;
  await b.close();
  process.stdout.write(`\rframe ${total}/${total} en ${((Date.now() - t0) / 1000).toFixed(1)}s\n`);

  const out = path.join(outDir, `${name}.mp4`);
  const audio = path.join(filmDir, "audio.wav");
  if (existsSync(audio) && !flag("no-audio")) {
    const l = loudnorm(audio, film.duration, silent, out);
    rmSync(silent);
    console.log(`audio: ${l.input.toFixed(1)} -> ${l.output.toFixed(1)} LUFS (true peak ${l.tp.toFixed(1)} dBTP)`);
  } else {
    spawnSync("mv", [silent, out]);
    if (!flag("no-audio")) console.log("aviso: sin audio.wav, el video sale mudo (correr npm run sound)");
  }
  console.log(out);
}

lint();
if (flag("check")) await check();
else if (frameArg !== null) await frame(frameArg);
else if (flag("sheet")) await sheet();
else await full();
