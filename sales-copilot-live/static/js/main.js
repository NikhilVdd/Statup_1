const nav = document.querySelector("[data-nav]");

if (nav) {
  const updateNav = () => {
    nav.classList.toggle("nav-scrolled", window.scrollY > 20);
  };

  updateNav();
  window.addEventListener("scroll", updateNav, { passive: true });
}

const revealTargets = document.querySelectorAll(".section-wrap, .notes-section, .pricing-teaser, .blog-teaser, .feature-card, .capability-card, .price-card");

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  );

  revealTargets.forEach((target) => {
    target.classList.add("reveal-ready");
    revealObserver.observe(target);
  });
} else {
  revealTargets.forEach((target) => target.classList.add("is-visible"));
}

const companySearch = document.getElementById("companySearch");
const statusFilter = document.getElementById("statusFilter");

function filterCompanies() {
  const searchValue = (companySearch?.value || "").toLowerCase();
  const statusValue = statusFilter?.value || "";

  document.querySelectorAll(".company-data-row").forEach((row) => {
    const matchesSearch = row.dataset.search.toLowerCase().includes(searchValue);
    const matchesStatus = !statusValue || row.dataset.status === statusValue;
    row.style.display = matchesSearch && matchesStatus ? "" : "none";
  });
}

companySearch?.addEventListener("input", filterCompanies);
statusFilter?.addEventListener("change", filterCompanies);

document.querySelector("[data-copy-notes]")?.addEventListener("click", async (event) => {
  const text = document.getElementById("noteDetail")?.innerText || "";
  await navigator.clipboard.writeText(text);
  event.currentTarget.textContent = "Copied";
  setTimeout(() => {
    event.currentTarget.textContent = "Copy notes";
  }, 1200);
});

function formatDemoTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

document.querySelectorAll("[data-demo-timer]").forEach((timer) => {
  let elapsed = Number(timer.dataset.startSeconds || 0);
  timer.textContent = formatDemoTime(elapsed);

  setInterval(() => {
    elapsed = (elapsed + 1) % 600;
    timer.textContent = formatDemoTime(elapsed);
  }, 1000);
});

document.querySelectorAll("[data-score-ring]").forEach((ring, index) => {
  const valueNode = ring.querySelector("[data-score-value]");
  const baseScore = Number(ring.dataset.score || 82);
  let direction = 1;
  let score = baseScore;

  ring.style.setProperty("--score-percent", score);
  if (valueNode) {
    valueNode.textContent = score;
  }

  setInterval(() => {
    if (score >= baseScore + 5) direction = -1;
    if (score <= baseScore - 4) direction = 1;
    score += direction;
    ring.style.setProperty("--score-percent", score);
    if (valueNode) {
      valueNode.textContent = score;
    }
  }, 1400 + index * 220);
});
