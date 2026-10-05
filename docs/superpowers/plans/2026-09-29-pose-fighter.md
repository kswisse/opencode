# Pose Fighter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a browser pose-controlled fighting game (player vs boss) in exactly 3 code files under `C:\Opencode\teachable machine\`, driven by a Teachable Machine pose model plus arrow keys.

**Architecture:** Single static page — `index.html` hosts a game `<canvas>`, a fixed webcam pane bottom-left, HUD bars, and overlay screens (home / win / lose / banners). `style.css` styles everything outside canvas drawing. `stretch.js` holds a single `requestAnimationFrame` loop with a `state` machine (`home → loading → playing → won | lost`), plain-object game entities, keyboard input gated by current pose class, and async pose detection via `@teachablemachine/pose` from CDN.

**Tech Stack:** Vanilla HTML/CSS/JS, Canvas 2D, TensorFlow.js + Teachable Machine Pose (CDN), no build step, no framework.

## Global Constraints

- Files: exactly `index.html`, `style.css`, `stretch.js` (plus existing `player.png`, `boss.png`) in `C:\Opencode\teachable machine\`.
- No build step, no npm, no framework. Open `index.html` in Chrome → runs.
- Player HP = 1200, Boss HP = 1200 (spec: equal).
- Skill 1: 100 dmg, 3s cooldown, straight projectile. Skill 2: 150 dmg, 5s cooldown, pink reticle on boss, damage lands 1s later. Shield: no cooldown, reduces incoming damage to 1/4, active only while pose X held. Idle: heal 5 HP/s, and only when pose is idle AND player is not pressing movement keys.
- Boss: shot 100 dmg / 3s; slash 150 dmg / 4s only when player within 220px; shield every 8–12s lasting 2s reducing incoming to 1/4.
- Arrow keys act ONLY when current pose is idle (or pose system unavailable → keys always act, so game is playable keyboard-only).
- Webcam pane: fixed bottom-left, ~240px wide, label + current pose class + confidence text.
- `MODEL_URL` constant at top of `stretch.js`; empty by default, user pastes their Teachable Machine Export URL.
- Pose class names mapped via `POSE_MAP` object; must tolerate unknown/missing class names.
- Image fallback: if `player.png`/`boss.png` fail to load, draw simple canvas shapes instead.
- Win overlay: grand "CHIẾN THẮNG" (gradient gold, glow pulse, falling confetti). Lose overlay: plain "BẠN ĐÃ THUA". Both have replay button; `R` restarts.
- Home screen before anything: game title + "BẮT ĐẦU" button; camera/model only initialized after that click.
- Language of all UI text: Vietnamese.
- Commit after each task (repo root `C:\Opencode`, commit only files under `teachable machine/` and `docs/`).

---

### Task 1: Page scaffold — index.html + style.css

**Files:**
- Create: `C:\Opencode\teachable machine\index.html`
- Create: `C:\Opencode\teachable machine\style.css`

**Interfaces:**
- Produces: DOM contract consumed by `stretch.js` in later tasks — element IDs listed below must exist exactly.

DOM contract (all IDs used by later tasks):
`#game` (canvas 960×540), `#hud` containing `#hp-player-fill`, `#hp-player-num`, `#hp-boss-fill`, `#hp-boss-num`, `#cooldowns` containing `#cd1`, `#cd2`, `#cd3`; `#webcam-wrap` containing `#video` (mirrored), `#pose-label`; overlays `#overlay` with `#overlay-title`, `#overlay-sub`, `#overlay-btn`, `#banner` (small transient message); scripts `@tensorflow/tfjs`, `@teachablemachine/pose`, then `stretch.js`.

- [ ] **Step 1: Write `index.html`**

```html
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pose Fighter</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div id="app">
  <header id="hud">
    <div class="hp-block">
      <span class="hp-name">BẠN</span>
      <div class="hp-bar"><div id="hp-player-fill" class="hp-fill player"></div></div>
      <span id="hp-player-num" class="hp-num">1200</span>
    </div>
    <div id="cooldowns">
      <div class="cd-slot" id="cd1"><span class="cd-key">1</span><span class="cd-name">Bắn</span></div>
      <div class="cd-slot" id="cd2"><span class="cd-key">2</span><span class="cd-name">Cầu nổ</span></div>
      <div class="cd-slot" id="cd3"><span class="cd-key">3</span><span class="cd-name">Khiên</span></div>
    </div>
    <div class="hp-block boss">
      <span id="hp-boss-num" class="hp-num">1200</span>
      <div class="hp-bar"><div id="hp-boss-fill" class="hp-fill boss"></div></div>
      <span class="hp-name">BOSS</span>
    </div>
  </header>

  <main id="stage">
    <canvas id="game" width="960" height="540"></canvas>

    <div id="webcam-wrap">
      <video id="video" autoplay playsinline muted></video>
      <div id="pose-label">Camera: tắt</div>
    </div>

    <div id="banner" class="hidden"></div>

    <div id="overlay">
      <h1 id="overlay-title">POSE FIGHTER</h1>
      <p id="overlay-sub">Goku vs Boss — điều khiển bằng tư thế qua camera</p>
      <button id="overlay-btn">BẮT ĐẦU</button>
      <p id="overlay-hint">Tay trái = bắn · Tay phải = cầu nổ · Tay X = khiên · Đứng thẳng = di chuyển</p>
    </div>
  </main>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@1.3.18/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@teachablemachine/pose@0.8/dist/teachablemachine-pose.min.js"></script>
<script src="stretch.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write `style.css`**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --hud-h: 76px;
  --gold: #ffd54a;
}

body {
  background: #0d1030;
  color: #fff;
  font-family: "Segoe UI", Arial, sans-serif;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

#app { width: min(960px, 100vw); padding: 10px; }

#hud {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 4px;
}

.hp-block { display: flex; align-items: center; gap: 8px; flex: 1; }
.hp-block.boss { justify-content: flex-end; }
.hp-name { font-weight: 700; letter-spacing: 2px; font-size: 14px; }
.hp-bar {
  flex: 1;
  height: 20px;
  background: #262a4d;
  border: 2px solid #454a7a;
  border-radius: 10px;
  overflow: hidden;
}
.hp-fill { height: 100%; width: 100%; transition: width .25s ease; }
.hp-fill.player { background: linear-gradient(90deg, #37d67a, #a5f3c4); }
.hp-fill.boss { background: linear-gradient(90deg, #ff5252, #ff8a80); }
.hp-num { font-variant-numeric: tabular-nums; font-weight: 700; min-width: 46px; text-align: center; }

#cooldowns { display: flex; gap: 8px; }
.cd-slot {
  width: 62px;
  padding: 4px 0;
  text-align: center;
  background: #1b1f45;
  border: 2px solid #454a7a;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}
.cd-slot .cd-key { display: block; font-weight: 800; font-size: 16px; }
.cd-slot .cd-name { font-size: 10px; opacity: .8; }
.cd-slot::after {
  content: "";
  position: absolute;
  left: 0; bottom: 0;
  width: 100%;
  height: 0%;
  background: rgba(255, 213, 74, .35);
  pointer-events: none;
}
.cd-slot.ready { border-color: var(--gold); }

#stage { position: relative; }

#game {
  display: block;
  width: 100%;
  height: auto;
  background: #000;
  border: 3px solid #454a7a;
  border-radius: 10px;
}

#webcam-wrap {
  position: fixed;
  left: 14px;
  bottom: 14px;
  width: 240px;
  z-index: 30;
  background: #11152e;
  border: 3px solid var(--gold);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0,0,0,.55);
}
#video {
  display: block;
  width: 100%;
  transform: scaleX(-1);
  background: #000;
}
#pose-label {
  font-size: 12px;
  padding: 4px 6px;
  text-align: center;
  background: #1b1f45;
}

#banner {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(20, 24, 60, .92);
  border: 1px solid var(--gold);
  color: var(--gold);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 20;
  max-width: 80%;
  text-align: center;
}
.hidden { display: none !important; }

#overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: rgba(8, 10, 34, .88);
  border-radius: 10px;
  z-index: 40;
  text-align: center;
  padding: 20px;
}
#overlay.hidden { display: none !important; }

#overlay-title {
  font-size: 58px;
  letter-spacing: 6px;
  background: linear-gradient(180deg, #fff3b0, var(--gold), #ff9100);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 18px rgba(255, 213, 74, .55));
}
#overlay-title.win { animation: pulse 1.1s ease-in-out infinite; }
#overlay-title.lose {
  background: none;
  color: #9aa0c3;
  font-size: 40px;
  filter: none;
}
#overlay-sub { font-size: 16px; color: #c6cbee; }
#overlay-hint { font-size: 13px; color: #8b91bd; max-width: 520px; }

#overlay-btn {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 3px;
  padding: 14px 46px;
  border: none;
  border-radius: 40px;
  cursor: pointer;
  color: #2a1c00;
  background: linear-gradient(180deg, #ffe27a, var(--gold));
  box-shadow: 0 6px 0 #b8860b, 0 12px 24px rgba(0,0,0,.4);
  transition: transform .1s ease;
}
#overlay-btn:active { transform: translateY(4px); box-shadow: 0 2px 0 #b8860b; }

#confetti-layer { position: absolute; inset: 0; pointer-events: none; z-index: 35; overflow: hidden; }
.confetti {
  position: absolute;
  top: -16px;
  width: 10px;
  height: 14px;
  border-radius: 2px;
  animation: fall linear forwards;
}
@keyframes fall {
  to { transform: translateY(560px) rotate(720deg); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 12px rgba(255,213,74,.5)); }
  50% { transform: scale(1.06); filter: drop-shadow(0 0 32px rgba(255,213,74,.95)); }
}
```

- [ ] **Step 3: Verify in browser**

Run: open `C:\Opencode\teachable machine\index.html` in Chrome.
Expected: dark page, HUD with two green/red HP bars reading 1200, 3 cooldown slots, black canvas, gold-bordered webcam pane bottom-left saying "Camera: tắt", centered overlay with title "POSE FIGHTER" and "BẮT ĐẦU" button. No console errors.

- [ ] **Step 4: Commit**

```powershell
git add "teachable machine/index.html" "teachable machine/style.css"
git commit -m "feat(pose-fighter): page scaffold with HUD, webcam pane, overlay"
```

---

### Task 2: Game core — state machine, sprites, render loop

**Files:**
- Create: `C:\Opencode\teachable machine\stretch.js`

**Interfaces:**
- Consumes: DOM ids from Task 1, images `player.png` / `boss.png` (already present).
- Produces (used by later tasks): global objects/functions with exact names:
  - `STATE` = `{ current: 'home'|'loading'|'playing'|'won'|'lost', pose: 'idle'|'skill1'|'skill2'|'shield', poseAvailable: bool, poseConfidence: number }`
  - `player = { x, y, w, h, hp, maxHp, facing, vy, onGround, crouch, invulnUntil }`
  - `boss = { x, y, w, h, hp, maxHp, shieldUntil, nextShotAt, nextSlashAt, nextShieldAt }`
  - `images = { player: Image|null, boss: Image|null }` plus `drawFallback(ctx, kind, x, y, w, h)`
  - `update(dt, now)` and `render(ctx, now)` — pure-ish game logic called by the loop
  - `resetGame()` — restore both fighters to initial values
  - `showOverlay(title, sub, btnText, mode)` where mode ∈ `'home'|'win'|'lose'`
  - `showBanner(text, ms)` / `hideBanner()`
  - `tick(now)` — rAF loop, dt in seconds clamped to 0.05

- [ ] **Step 1: Write skeleton of `stretch.js` (DOM refs, constants, state, images, helpers, loop)**

```javascript
"use strict";

/* ===== CẤU HÌNH ===== */
const MODEL_URL = ""; // ← dán URL model Teachable Machine vào đây (Export → Tensorflow.js)
const POSE_MAP = {
  // gán TÊN CLASS trong model của bạn vào 4 hành động:
  "skill1": "skill1",   // giơ tay trái
  "skill2": "skill2",   // giơ tay phải
  "shield": "shield",   // dấu X
  "idle": "idle"        // đứng thẳng
};

const WORLD = { w: 960, h: 540, groundY: 470 };
const PLAYER_MAX_HP = 1200;
const BOSS_MAX_HP = 1200;
const SKILL1 = { dmg: 100, cd: 3000, speed: 620 };
const SKILL2 = { dmg: 150, cd: 5000, fuse: 1000 };
const BOSS_CFG = { shotDmg: 100, shotCd: 3000, slashDmg: 150, slashCd: 4000, slashRange: 220, shieldCdMin: 8000, shieldCdMax: 12000, shieldDur: 2000 };
const HEAL_PER_SEC = 5;
const SHIELD_FACTOR = 0.25;

/* ===== DOM ===== */
const $ = (id) => document.getElementById(id);
const canvas = $("game");
const ctx = canvas.getContext("2d");
const video = $("video");
const poseLabel = $("pose-label");
const overlay = $("overlay");
const overlayTitle = $("overlay-title");
const overlaySub = $("overlay-sub");
const overlayBtn = $("overlay-btn");
const bannerEl = $("banner");

/* ===== STATE ===== */
const STATE = {
  current: "home",       // home | loading | playing | won | lost
  pose: "idle",          // idle | skill1 | skill2 | shield
  poseAvailable: false,  // model + camera đã sẵn sàng?
  poseConfidence: 0,
  poseChangedAt: 0
};

const player = {
  x: 160, y: WORLD.groundY, w: 90, h: 140,
  hp: PLAYER_MAX_HP, maxHp: PLAYER_MAX_HP,
  facing: 1, vy: 0, onGround: true, crouch: false,
  invulnUntil: 0,
  cd1: 0, cd2: 0       // thời điểm hết hồi chiêu (ms)
};
const boss = {
  x: 720, y: WORLD.groundY, w: 110, h: 160,
  hp: BOSS_MAX_HP, maxHp: BOSS_MAX_HP,
  shieldUntil: 0, nextShotAt: 0, nextSlashAt: 0, nextShieldAt: 0
};

const keys = Object.create(null);
let projectiles = [];   // đạn của player & boss
let bursts = [];        // hiệu ứng nổ
let reticles = [];      // hồng tâm skill 2
let slashes = [];       // hiệu ứng chém

const images = { player: null, boss: null };
function loadImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => { console.warn("Không tải được " + src + " → dùng hình vẽ thay thế"); resolve(null); };
    img.src = src;
  });
}

function drawFallback(c, kind, x, y, w, h) {
  c.save();
  if (kind === "player") {
    c.fillStyle = "#4fc3f7";
    c.beginPath(); c.arc(x + w / 2, y - 26, 26, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#29b6f6";
    c.fillRect(x + w / 2 - 24, y - 48, 48, 14);
    c.fillStyle = "#81d4fa";
    c.fillRect(x + 14, y - h + 34, w - 28, h - 34);
  } else {
    c.fillStyle = "#ce93d8";
    c.beginPath(); c.arc(x + w / 2, y - 30, 30, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#ba68c8";
    c.fillRect(x + 8, y - h + 40, w - 16, h - 40);
    c.fillStyle = "#f3e5f5";
    c.fillRect(x + w / 2 - 16, y - 64, 32, 10);
  }
  c.restore();
}

function drawFighter(c, img, fallbackKind, e, now) {
  const bob = e.onGround === false ? 0 : Math.sin(now / 320 + e.x) * 2;
  const drawW = e.w, drawH = e.h;
  const drawX = e.x - drawW / 2;
  const drawY = e.y - drawH + bob;
  c.save();
  if (img) {
    if (e.facing && e.facing < 0) {
      c.translate(e.x, 0); c.scale(-1, 1); c.translate(-e.x, 0);
    }
    c.drawImage(img, drawX, drawY, drawW, drawH);
  } else {
    drawFallback(c, fallbackKind, drawX, e.y + bob, drawW, drawH);
  }
  c.restore();
}

function showOverlay(title, sub, btnText, mode) {
  overlayTitle.textContent = title;
  overlaySub.textContent = sub;
  overlayBtn.textContent = btnText;
  overlayTitle.className = mode === "win" ? "win" : mode === "lose" ? "lose" : "";
  overlay.classList.remove("hidden");
}
function hideOverlay() { overlay.classList.add("hidden"); }

let bannerTimer = 0;
function showBanner(text, ms = 3000) {
  bannerEl.textContent = text;
  bannerEl.classList.remove("hidden");
  clearTimeout(bannerTimer);
  bannerTimer = setTimeout(hideBanner, ms);
}
function hideBanner() { bannerEl.classList.add("hidden"); }

function resetGame() {
  player.x = 160; player.hp = PLAYER_MAX_HP; player.facing = 1;
  player.vy = 0; player.crouch = false; player.invulnUntil = 0;
  player.cd1 = 0; player.cd2 = 0;
  boss.x = 720; boss.hp = BOSS_MAX_HP; boss.shieldUntil = 0;
  const now = performance.now();
  boss.nextShotAt = now + 2500;
  boss.nextSlashAt = now + 4000;
  boss.nextShieldAt = now + (BOSS_CFG.shieldCdMin + BOSS_CFG.shieldCdMax) / 2;
  projectiles = []; bursts = []; reticles = []; slashes = [];
}

function updateHUD() {
  $("hp-player-fill").style.width = Math.max(0, player.hp / player.maxHp * 100) + "%";
  $("hp-boss-fill").style.width = Math.max(0, boss.hp / boss.maxHp * 100) + "%";
  $("hp-player-num").textContent = Math.max(0, Math.ceil(player.hp));
  $("hp-boss-num").textContent = Math.max(0, Math.ceil(boss.hp));
}

function spawnConfetti() {
  const layer = document.createElement("div");
  layer.id = "confetti-layer";
  const colors = ["#ffd54a", "#ff6f00", "#fff176", "#ff4081", "#69f0ae", "#40c4ff"];
  for (let i = 0; i < 90; i++) {
    const p = document.createElement("div");
    p.className = "confetti";
    p.style.left = Math.random() * 100 + "%";
    p.style.background = colors[i % colors.length];
    p.style.animationDuration = (1.8 + Math.random() * 2.2) + "s";
    p.style.animationDelay = (Math.random() * 1.4) + "s";
    layer.appendChild(p);
  }
  document.getElementById("stage").appendChild(layer);
  setTimeout(() => layer.remove(), 6000);
}
```

- [ ] **Step 2: Add input + home-screen wiring + rAF loop**

Append to `stretch.js`:

```javascript
/* ===== INPUT ===== */
window.addEventListener("keydown", (e) => {
  keys[e.key] = true;
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) e.preventDefault();
  if ((STATE.current === "won" || STATE.current === "lost") && (e.key === "r" || e.key === "R")) startPlaying();
  if (STATE.current !== "playing") return;
  // phím 1/2/3 là backup khi không có pose
  if (!STATE.poseAvailable) {
    if (e.key === "1") trySkill1();
    if (e.key === "2") trySkill2();
    if (e.key === "3") player.shieldByKey = true;
  }
});
window.addEventListener("keyup", (e) => {
  keys[e.key] = false;
  if (e.key === "3") player.shieldByKey = false;
});

/* ===== GAME LOOP ===== */
function tick(now) {
  requestAnimationFrame(tick);
  if (STATE.last == null) STATE.last = now;
  let dt = Math.min((now - STATE.last) / 1000, 0.05);
  STATE.last = now;
  if (STATE.current === "playing") update(dt, now);
  render(ctx, now);
  updateHUD();
}

window.addEventListener("DOMContentLoaded", async () => {
  [images.player, images.boss] = await Promise.all([
    loadImage("player.png"), loadImage("boss.png")
  ]);
  overlayBtn.addEventListener("click", () => {
    if (STATE.current === "home") startGame();
    else startPlaying();
  });
  resetGame();
  requestAnimationFrame(tick);
});
```

Note: `trySkill1`, `trySkill2`, `startGame`, `startPlaying`, `update`, `render` are defined in Tasks 3–5 — the page will throw until they exist, so implement Tasks 3–5 before browser verification.

- [ ] **Step 3: Commit (no browser check yet — Task 5 completes the loop)**

```powershell
git add "teachable machine/stretch.js"
git commit -m "feat(pose-fighter): core state, sprites, HUD, input scaffold"
```

---

### Task 3: Player combat — skills, shield, healing, movement

**Files:**
- Modify: `C:\Opencode\teachable machine\stretch.js`

**Interfaces:**
- Consumes: `STATE`, `player`, `boss`, `keys`, `SKILL1`, `SKILL2`, `HEAL_PER_SEC`, `SHIELD_FACTOR`, `showBanner`, `projectiles`, `reticles`, `bursts` from Task 2.
- Produces: `trySkill1()`, `trySkill2()`, `playerHasShield(now)`, `applyDamageTo(target, amount, now, sourceX)` used by Task 4 (boss AI attacks player) and Task 5 (rendering).

- [ ] **Step 1: Append combat logic**

```javascript
/* ===== PLAYER COMBAT ===== */
function playerHasShield(now) {
  if (STATE.pose === "shield" && STATE.poseAvailable) return true;
  return !!player.shieldByKey;
}

function trySkill1(now = performance.now()) {
  if (STATE.current !== "playing") return;
  if (now < player.cd1) { showBanner("Skill 1 đang hồi chiêu", 1200); return; }
  player.cd1 = now + SKILL1.cd;
  projectiles.push({
    owner: "player",
    x: player.x + player.facing * 40,
    y: player.y - player.h * 0.6,
    vx: SKILL1.speed,
    dmg: SKILL1.dmg,
    r: 9
  });
}

function trySkill2(now = performance.now()) {
  if (STATE.current !== "playing") return;
  if (now < player.cd2) { showBanner("Skill 2 đang hồi chiêu", 1200); return; }
  player.cd2 = now + SKILL2.cd;
  reticles.push({ x: boss.x, y: boss.y - boss.h * 0.5, explodeAt: now + SKILL2.fuse, dmg: SKILL2.dmg, r: 46 });
}

function applyDamageTo(target, amount, now) {
  if (target === player && now < player.invulnUntil) return;
  const shielding = target === player
    ? playerHasShield(now)
    : now < boss.shieldUntil;
  const real = shielding ? Math.ceil(amount * SHIELD_FACTOR) : amount;
  target.hp -= real;
  if (target === player) player.invulnUntil = now + 400;
  bursts.push({ x: target.x, y: target.y - target.h * 0.5, born: now, text: "-" + real, shielded: shielding });
}

function movementAllowsKeys(now) {
  // phím mũi tên chỉ chạy khi pose idle (hoặc không có pose system)
  if (STATE.poseAvailable && STATE.pose !== "idle") return false;
  return true;
}

function updatePlayer(dt, now) {
  const canMove = movementAllowsKeys(now);
  player.crouch = canMove && !!keys["ArrowDown"] && player.onGround;

  let vx = 0;
  if (canMove && !player.crouch) {
    if (keys["ArrowRight"]) { vx = 230; player.facing = 1; }
    if (keys["ArrowLeft"]) { vx = -230; player.facing = -1; }
  }
  player.x = Math.max(40, Math.min(WORLD.w - 40, player.x + vx * dt));

  if (canMove && keys["ArrowUp"] && player.onGround) {
    player.vy = -560;
    player.onGround = false;
  }
  player.vy += 1400 * dt;
  player.y += player.vy * dt;
  if (player.y >= WORLD.groundY) {
    player.y = WORLD.groundY;
    player.vy = 0;
    player.onGround = true;
  }

  // pose skill kích hoạt chiêu
  if (STATE.poseAvailable && STATE.current === "playing") {
    if (STATE.pose === "skill1") trySkill1(now);
    if (STATE.pose === "skill2") trySkill2(now);
  }

  // hồi máu khi đứng yên thật sự
  const idleOk = STATE.poseAvailable ? STATE.pose === "idle" : true;
  const pressing = keys["ArrowLeft"] || keys["ArrowRight"] || keys["ArrowUp"] || keys["ArrowDown"];
  if (idleOk && !pressing && player.hp > 0) {
    player.hp = Math.min(player.maxHp, player.hp + HEAL_PER_SEC * dt);
  }
}
```

- [ ] **Step 2: Commit**

```powershell
git add "teachable machine/stretch.js"
git commit -m "feat(pose-fighter): player skills, shield, healing, movement gate"
```

---

### Task 4: Boss AI + projectiles + win/lose

**Files:**
- Modify: `C:\Opencode\teachable machine\stretch.js`

**Interfaces:**
- Consumes: `applyDamageTo(target, amount, now)` (Task 3), `boss.nextShotAt` / `nextSlashAt` / `nextShieldAt` / `shieldUntil` fields (Task 2).
- Produces: `updateBoss(dt, now)`, `updateProjectiles(dt, now)`, `updateEffects(now)`, `checkEnd(now)` used by `update()` in Task 5; `startGame()`, `startPlaying()` called from Task 2 wiring.

- [ ] **Step 1: Append boss AI**

```javascript
/* ===== BOSS AI ===== */
function updateBoss(dt, now) {
  if (boss.hp <= 0) return;
  const dist = Math.abs(boss.x - player.x);

  boss.facing = player.x < boss.x ? -1 : 1;

  if (now >= boss.nextShotAt) {
    boss.nextShotAt = now + BOSS_CFG.shotCd;
    projectiles.push({
      owner: "boss",
      x: boss.x + boss.facing * 45,
      y: boss.y - boss.h * 0.62,
      vx: boss.facing * 540,
      dmg: BOSS_CFG.shotDmg,
      r: 11
    });
  }

  if (dist < BOSS_CFG.slashRange && now >= boss.nextSlashAt && player.onGround) {
    boss.nextSlashAt = now + BOSS_CFG.slashCd;
    slashes.push({ x: player.x, y: player.y - player.h * 0.5, born: now });
    applyDamageTo(player, BOSS_CFG.slashDmg, now);
  }

  if (now >= boss.nextShieldAt) {
    boss.shieldUntil = now + BOSS_CFG.shieldDur;
    boss.nextShieldAt = now + BOSS_CFG.shieldCdMin +
      Math.random() * (BOSS_CFG.shieldCdMax - BOSS_CFG.shieldCdMin);
  }
}

/* ===== ĐẠN / HIỆU ỨNG ===== */
function updateProjectiles(dt, now) {
  for (let i = projectiles.length - 1; i >= 0; i--) {
    const p = projectiles[i];
    p.x += p.vx * dt;
    if (p.x < -40 || p.x > WORLD.w + 40) { projectiles.splice(i, 1); continue; }
    if (p.owner === "player") {
      if (Math.abs(p.x - boss.x) < boss.w / 2 + p.r &&
          p.y > boss.y - boss.h && p.y < boss.y + 10) {
        applyDamageTo(boss, p.dmg, now);
        bursts.push({ x: p.x, y: p.y, born: now, text: "-" + p.dmg, shielded: now < boss.shieldUntil });
        projectiles.splice(i, 1);
      }
    } else {
      const ph = player.crouch ? player.h * 0.55 : player.h;
      if (Math.abs(p.x - player.x) < player.w / 2 + p.r &&
          p.y > player.y - ph && p.y < player.y + 10) {
        applyDamageTo(player, p.dmg, now);
        bursts.push({ x: p.x, y: p.y, born: now, text: "-" + p.dmg, shielded: playerHasShield(now) });
        projectiles.splice(i, 1);
      }
    }
  }
}

function updateEffects(now) {
  for (let i = reticles.length - 1; i >= 0; i--) {
    const r = reticles[i];
    if (now >= r.explodeAt) {
      applyDamageTo(boss, r.dmg, now);
      bursts.push({ x: r.x, y: r.y, born: now, text: "-" + r.dmg, shielded: now < boss.shieldUntil, big: true });
      projectiles = projectiles.filter(p => p.owner === "boss" && Math.abs(p.x - r.x) > 90);
      reticles.splice(i, 1);
    }
  }
  bursts = bursts.filter(b => now - b.born < 900);
  slashes = slashes.filter(s => now - s.born < 300);
}

function checkEnd(now) {
  if (STATE.current !== "playing") return;
  if (boss.hp <= 0) {
    boss.hp = 0;
    STATE.current = "won";
    showOverlay("CHIẾN THẮNG", "Boss đã bị hạ gục — warrior giỏi lắm!", "CHƠI LẠI", "win");
    spawnConfetti();
  } else if (player.hp <= 0) {
    player.hp = 0;
    STATE.current = "lost";
    showOverlay("BẠN ĐÃ THUA", "Thử lại nào — bấm nút hoặc nhấn R", "CHƠI LẠI", "lose");
  }
}
```

- [ ] **Step 2: Append game start/restart functions**

```javascript
/* ===== BẮT ĐẦU / CHƠI LẠI ===== */
async function startGame() {
  STATE.current = "loading";
  showOverlay("ĐANG TẢI…", "Đang khởi tạo model và camera", "", "home");
  overlayBtn.style.display = "none";
  try {
    await initPose();
  } catch (err) {
    console.warn(err);
    showBanner("Không khởi tạo được pose — chơi bằng phím 1/2/3 nhé!", 6000);
  }
  overlayBtn.style.display = "";
  startPlaying();
}

function startPlaying() {
  resetGame();
  STATE.current = "playing";
  hideOverlay();
  if (!STATE.poseAvailable) {
    showBanner("Chế độ phím: 1 = bắn, 2 = cầu nổ, 3 = khiên, ↑↓←→ di chuyển", 6000);
  }
}
```

- [ ] **Step 3: Commit**

```powershell
git add "teachable machine/stretch.js"
git commit -m "feat(pose-fighter): boss AI, projectiles, win-lose, restart flow"
```

---

### Task 5: Render + `update()` glue (completes the loop from Task 2)

**Files:**
- Modify: `C:\Opencode\teachable machine\stretch.js`

**Interfaces:**
- Consumes: `updatePlayer` (Task 3), `updateBoss`, `updateProjectiles`, `updateEffects`, `checkEnd` (Task 4), render helpers from Task 2.
- Produces: `update(dt, now)` and `render(ctx, now)` — the two functions Task 2's `tick()` already calls.

- [ ] **Step 1: Append update() and render()**

```javascript
/* ===== UPDATE ===== */
function update(dt, now) {
  updatePlayer(dt, now);
  updateBoss(dt, now);
  updateProjectiles(dt, now);
  updateEffects(now);
  checkEnd(now);
}

/* ===== RENDER ===== */
function drawBackground(c) {
  const sky = c.createLinearGradient(0, 0, 0, WORLD.h);
  sky.addColorStop(0, "#2b1055");
  sky.addColorStop(0.55, "#5c2a8a");
  sky.addColorStop(1, "#ff7e5f");
  c.fillStyle = sky;
  c.fillRect(0, 0, WORLD.w, WORLD.h);

  c.fillStyle = "rgba(255,255,255,.85)";
  for (let i = 0; i < 40; i++) {
    const sx = (i * 137) % WORLD.w;
    const sy = (i * 61) % 220;
    c.fillRect(sx, sy, 2, 2);
  }

  c.fillStyle = "#1b5e20";
  c.beginPath();
  c.moveTo(0, WORLD.groundY);
  c.quadraticCurveTo(240, WORLD.groundY - 70, 480, WORLD.groundY);
  c.quadraticCurveTo(720, WORLD.groundY - 90, WORLD.w, WORLD.groundY);
  c.lineTo(WORLD.w, WORLD.h); c.lineTo(0, WORLD.h);
  c.closePath(); c.fill();

  c.fillStyle = "#2e7d32";
  c.fillRect(0, WORLD.groundY, WORLD.w, WORLD.h - WORLD.groundY);
}

function drawShield(c, e, now, isBoss) {
  const active = isBoss ? now < e.shieldUntil : playerHasShield(now);
  if (!active) return;
  c.save();
  c.strokeStyle = "rgba(120, 220, 255, .95)";
  c.fillStyle = "rgba(120, 220, 255, .22)";
  c.lineWidth = 5;
  const r = Math.max(e.w, e.h) * 0.72;
  const dir = isBoss ? -1 : 1;
  c.beginPath();
  c.arc(e.x + dir * 34, e.y - e.h * 0.5, r, -Math.PI * 0.75, Math.PI * 0.75);
  c.stroke();
  c.beginPath();
  c.arc(e.x + dir * 34, e.y - e.h * 0.5, r, -Math.PI * 0.75, Math.PI * 0.75);
  c.fill();
  c.restore();
}

function render(c, now) {
  c.clearRect(0, 0, WORLD.w, WORLD.h);
  drawBackground(c);

  if (STATE.current === "home" || STATE.current === "loading") {
    return;
  }

  drawShield(c, boss, now, true);
  drawFighter(c, images.boss, "boss", boss, now);
  drawShield(c, player, now, false);
  drawFighter(c, images.player, "player", player, now);

  for (const r of reticles) {
    const t = (r.explodeAt - now) / SKILL2.fuse;
    c.save();
    c.strokeStyle = "#ff4d94";
    c.lineWidth = 4;
    c.beginPath(); c.arc(r.x, r.y, r.r, 0, Math.PI * 2); c.stroke();
    c.beginPath(); c.arc(r.x, r.y, r.r * (1 - t), 0, Math.PI * 2); c.stroke();
    c.beginPath();
    c.moveTo(r.x - r.r * 1.3, r.y); c.lineTo(r.x + r.r * 1.3, r.y);
    c.moveTo(r.x, r.y - r.r * 1.3); c.lineTo(r.x, r.y + r.r * 1.3);
    c.stroke();
    c.fillStyle = "rgba(255,77,148,.2)";
    c.beginPath(); c.arc(r.x, r.y, r.r, 0, Math.PI * 2); c.fill();
    c.restore();
  }

  for (const p of projectiles) {
    c.save();
    c.fillStyle = p.owner === "player" ? "#ffe27a" : "#ff5252";
    c.shadowColor = c.fillStyle;
    c.shadowBlur = 14;
    c.beginPath(); c.arc(p.x, p.y, p.r, 0, Math.PI * 2); c.fill();
    c.restore();
  }

  for (const s of slashes) {
    const a = 1 - (now - s.born) / 300;
    c.save();
    c.globalAlpha = a;
    c.strokeStyle = "#fff";
    c.lineWidth = 7;
    c.beginPath();
    c.arc(s.x, s.y, 60, -Math.PI * 0.8, Math.PI * 0.3);
    c.stroke();
    c.restore();
  }

  for (const b of bursts) {
    const age = (now - b.born) / 900;
    c.save();
    c.globalAlpha = 1 - age;
    c.fillStyle = b.shielded ? "#78dcff" : b.big ? "#ff4d94" : "#fff";
    c.font = (b.big ? "bold 40px" : "bold 24px") + " Segoe UI";
    c.textAlign = "center";
    c.fillText(b.text, b.x, b.y - age * 46);
    c.restore();
  }

  drawCooldownOverlays(c, now);
}

function drawCooldownOverlays(c, now) {
  const set = (id, readyIn, total) => {
    const el = $(id);
    const pct = readyIn > 0 ? Math.max(0, Math.min(100, readyIn / total * 100)) : 0;
    el.style.setProperty("--x", pct + "%");
    el.classList.toggle("ready", readyIn <= 0);
    el.querySelector ? null : null;
    el.style.setProperty("height", "");
    const after = pct;
    el.setAttribute("data-pct", after);
    el.style.cssText = el.style.cssText.replace(/--cd-pct:[^;]+;?/, "");
    el.style.setProperty("--cd-pct", after + "%");
  };
  set("cd1", player.cd1 - now, SKILL1.cd);
  set("cd2", player.cd2 - now, SKILL2.cd);
  set("cd3", playerHasShield(now) ? 1 : 0, 1);
}
```

Fix the CSS cooldown overlay to read `--cd-pct` — append to `style.css`:

```css
.cd-slot::after { height: var(--cd-pct, 0%); }
.cd-slot.ready::after { height: 0%; }
```

Note: simplify `set()` — the messy `cssText` lines above are wrong. Replace the body of `set` with:

```javascript
const set = (id, readyIn, total) => {
  const el = $(id);
  const pct = readyIn > 0 ? Math.max(0, Math.min(100, (readyIn / total) * 100)) : 0;
  el.style.setProperty("--cd-pct", pct + "%");
  el.classList.toggle("ready", readyIn <= 0);
};
```

- [ ] **Step 2: Browser verification of core loop (pose not wired yet — Task 6)**

Run: open `index.html` in Chrome.
Expected: home screen → click **BẮT ĐẦU** → banner appears saying pose init failed or "Chế độ phím…" (because `initPose` is not defined until Task 6 — add a temporary `async function initPose() {}` stub at the end of the file now, to be replaced in Task 6). Game renders: player sprite left, boss right, background. Verify:
1. Arrow keys move/jump/crouch (poseAvailable=false → keys always work).
2. Press `1` → golden projectile flies right, hits boss for 100, HP bar drops to 1100; cooldown slot 1 shows yellow fill for 3s.
3. Press `2` → pink reticle on boss, after 1s explosion −150, slot 2 on cooldown 5s.
4. Press `3` → cyan shield arc; boss shot shows −25 instead of −100 when it lands.
5. Walk close to boss → slash −150 every ~4s.
6. Let boss hit you until HP 0 → "BẠN ĐÃ THUA" + R restarts.
7. `console.log` errors → none.

- [ ] **Step 3: Commit**

```powershell
git add "teachable machine/stretch.js" "teachable machine/style.css"
git commit -m "feat(pose-fighter): render pipeline and update glue"
```

---

### Task 6: Pose detection integration

**Files:**
- Modify: `C:\Opencode\teachable machine\stretch.js`

**Interfaces:**
- Consumes: `MODEL_URL`, `POSE_MAP` (Task 2), `STATE.pose`/`poseAvailable`/`poseConfidence` (Task 2), `video` + `poseLabel` DOM.
- Produces: `initPose()` — async, resolves when model loaded + camera started (or throws; `startGame` in Task 4 already catches).

- [ ] **Step 1: Replace the `initPose` stub with the real implementation**

```javascript
/* ===== POSE DETECTION ===== */
let poseModel = null, poseDetectorLoop = null, lastPose = "idle";

function resolveClass(className) {
  if (!className) return null;
  const c = className.trim().toLowerCase();
  for (const [action, key] of Object.entries(POSE_MAP)) {
    if ((key && key.toLowerCase() === c) || action === c) return action;
  }
  // fallback: khớp theo index nếu tên class trong model khác hoàn toàn
  return null;
}

async function initPose() {
  if (!MODEL_URL) throw new Error("MODEL_URL chưa được điền");
  if (typeof tmPose === "undefined") throw new Error("Thư viện Teachable Machine chưa tải");

  showBanner("Đang tải model pose…", 10000);

  const canvasTM = document.createElement("canvas");
  canvasTM.width = 400; canvasTM.height = 300;
  const response = await fetch(MODEL_URL + "model.json");
  const model = await response.json();
  const metadata = await (await fetch(MODEL_URL + "metadata.json")).json();
  poseModel = await tmPose.loadFromURL(MODEL_URL + "model.json", metadata);

  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480, facingMode: "user" },
    audio: false
  });
  video.srcObject = stream;
  await new Promise((res) => { video.onloadedmetadata = () => res(); });
  await video.play();

  STATE.poseAvailable = true;
  hideBanner();
  showBanner("Pose đã sẵn sàng — chơi thôi!", 2500);
  startPoseLoop(canvasTM);
}

function startPoseLoop(canvasTM) {
  const cxtm = canvasTM.getContext("2d");
  const loop = async () => {
    if (!STATE.poseAvailable) return;
    try {
      const { pose, posenetOutput } = await poseModel.estimatePose(video);
      const prediction = await poseModel.predict(posenetOutput);
      let best = null;
      for (const p of prediction) {
        if (!best || p.probability > best.probability) best = p;
      }
      const mapped = resolveClass(best ? best.className : null);
      const conf = best ? best.probability : 0;

      if (mapped && conf >= 0.6) {
        if (mapped !== lastPose) { lastPose = mapped; STATE.poseChangedAt = performance.now(); }
        STATE.pose = mapped;
        STATE.poseConfidence = conf;
      } else if (performance.now() - STATE.poseChangedAt > 500) {
        STATE.pose = "idle";
        STATE.poseConfidence = conf;
      }
      poseLabel.textContent = "Pose: " + (best ? best.className : "?") +
        " (" + Math.round(STATE.poseConfidence * 100) + "%)";
    } catch (err) {
      console.warn("pose loop error", err);
    }
    poseDetectorLoop = setTimeout(loop, 120);
  };
  loop();
}
```

Note: remove the `model`/`metadata` pre-fetch lines if unused (`poseModel.estimatePose` works from `tmPose.loadFromURL`). Keep only `tmPose.loadFromURL`. Also `cxtm` is unused — drop `canvasTM` entirely if not needed by `estimatePose` (it accepts the `<video>` element directly). Final form should be:

```javascript
async function initPose() {
  if (!MODEL_URL) throw new Error("MODEL_URL chưa được điền");
  if (typeof tmPose === "undefined") throw new Error("Thư viện Teachable Machine chưa tải");

  showBanner("Đang tải model pose…", 10000);
  poseModel = await tmPose.loadFromURL(MODEL_URL + "model.json");

  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480, facingMode: "user" },
    audio: false
  });
  video.srcObject = stream;
  await new Promise((res) => { video.onloadedmetadata = () => res(); });
  await video.play();

  STATE.poseAvailable = true;
  hideBanner();
  showBanner("Pose đã sẵn sàng — chơi thôi!", 2500);
  startPoseLoop();
}
```

(with `startPoseLoop()` taking no canvas argument — see corrected loop above minus `canvasTM`.)

- [ ] **Step 2: Empty-URL path check**

Run: open `index.html`, click **BẮT ĐẦU** (leave `MODEL_URL = ""`).
Expected: quick fallback to "Chế độ phím" banner; webcam pane still shows "Camera: tắt"; game playable with `1`/`2`/`3` + arrows. No uncaught errors (initPose rejection is caught by `startGame`).

- [ ] **Step 3: Commit**

```powershell
git add "teachable machine/stretch.js"
git commit -m "feat(pose-fighter): Teachable Machine pose detection loop"
```

---

### Task 7: Final QA pass (spec test checklist)

**Files:**
- Modify: `C:\Opencode\teachable machine\stretch.js` (only if bugs found)

- [ ] **Step 1: Run the spec's manual test checklist**

Open `index.html` in Chrome with camera available and a trained model URL pasted into `MODEL_URL`:

| # | Action | Expected |
|---|---|---|
| 1 | Open page | Home screen: title "POSE FIGHTER", button "BẮT ĐẦU" |
| 2 | Click BẮT ĐẦU with empty `MODEL_URL` | "Chế độ phím" banner; game runs |
| 3 | Paste real model URL, reload, click start | Webcam shows, pose label updates |
| 4 | Giơ tay trái | Skill 1 fires, −100 on boss, slot 1 cooldown 3s |
| 5 | Giơ tay phải | Pink reticle → −150 after 1s, slot 2 cooldown 5s |
| 6 | Dấu X | Shield arc; boss shot deals −25 |
| 7 | Đứng thẳng + phím mũi tên | Moves/jump/crouch works |
| 8 | Pose skill + phím mũi tên | Movement blocked |
| 9 | Idle, không bấm phím | HP ticks up +5/s |
| 10 | Boss close | Slash −150 every ~4s |
| 11 | Boss HP → 0 | "CHIẾN THẮNG" gradient + pulse + confetti |
| 12 | Player HP → 0 | "BẠN ĐÃ THUA", R restarts |
| 13 | `player.png` renamed → reload | Fallback shapes drawn, no crash |
| 14 | Console | No uncaught errors |

- [ ] **Step 2: Fix any bugs found, commit**

```powershell
git add "teachable machine/"
git commit -m "fix(pose-fighter): QA fixes"
```
