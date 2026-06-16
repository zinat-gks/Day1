/* ============ INFO MODAL ============ */
const modal = document.getElementById("infoModal");
const openModal = () => { modal.classList.add("open"); modal.setAttribute("aria-hidden", "false"); };
const closeModal = () => { modal.classList.remove("open"); modal.setAttribute("aria-hidden", "true"); };

document.getElementById("getToKnowBtn").addEventListener("click", openModal);
modal.querySelectorAll("[data-close]").forEach(el => el.addEventListener("click", closeModal));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

/* smooth-scroll to cards */
document.getElementById("exploreBtn").addEventListener("click", () => {
  document.getElementById("cards").scrollIntoView({ behavior: "smooth" });
});

/* ============ SLIDER ============ */
const track = document.getElementById("track");
const cards = Array.from(track.children);
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const dotsWrap = document.getElementById("dots");
let index = 0;

/* build dots */
cards.forEach((_, i) => {
  const dot = document.createElement("button");
  dot.className = "dot" + (i === 0 ? " active" : "");
  dot.setAttribute("aria-label", `Go to card ${i + 1}`);
  dot.addEventListener("click", () => goTo(i));
  dotsWrap.appendChild(dot);
});
const dots = Array.from(dotsWrap.children);

function goTo(i) {
  index = Math.max(0, Math.min(i, cards.length - 1));
  track.style.transform = `translateX(-${index * 100}%)`;
  dots.forEach((d, k) => d.classList.toggle("active", k === index));
  prevBtn.style.opacity = index === 0 ? ".35" : "1";
  nextBtn.style.opacity = index === cards.length - 1 ? ".35" : "1";
}

prevBtn.addEventListener("click", () => goTo(index - 1));
nextBtn.addEventListener("click", () => goTo(index + 1));

/* keyboard arrows */
document.addEventListener("keydown", e => {
  if (e.key === "ArrowLeft") goTo(index - 1);
  if (e.key === "ArrowRight") goTo(index + 1);
});

/* ============ DRAG / SWIPE ============ */
let startX = 0, dragging = false;
const viewport = track.parentElement;

const getX = e => (e.touches ? e.touches[0].clientX : e.clientX);

function dragStart(e) { dragging = true; startX = getX(e); track.style.transition = "none"; }
function dragMove(e) {
  if (!dragging) return;
  const dx = getX(e) - startX;
  track.style.transform = `translateX(calc(-${index * 100}% + ${dx}px))`;
}
function dragEnd(e) {
  if (!dragging) return;
  dragging = false;
  track.style.transition = "";
  const dx = (e.changedTouches ? e.changedTouches[0].clientX : e.clientX) - startX;
  if (Math.abs(dx) > 60) goTo(index + (dx < 0 ? 1 : -1));
  else goTo(index);
}

viewport.addEventListener("mousedown", dragStart);
window.addEventListener("mousemove", dragMove);
window.addEventListener("mouseup", dragEnd);
viewport.addEventListener("touchstart", dragStart, { passive: true });
viewport.addEventListener("touchmove", dragMove, { passive: true });
viewport.addEventListener("touchend", dragEnd);

/* init */
goTo(0);
