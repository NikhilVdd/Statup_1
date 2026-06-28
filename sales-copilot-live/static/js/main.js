const nav = document.querySelector("[data-nav]");
const marketingPage = document.body.classList.contains("marketing-page");

if (marketingPage && window.matchMedia("(pointer: fine)").matches) {
  const cursor = document.createElement("div");
  cursor.className = "site-cursor";
  cursor.setAttribute("aria-hidden", "true");
  document.body.appendChild(cursor);
  document.body.classList.add("cursor-enhanced");

  window.addEventListener("pointermove", (event) => {
    cursor.style.left = `${event.clientX}px`;
    cursor.style.top = `${event.clientY}px`;
    cursor.classList.add("is-visible");
  });

  window.addEventListener("pointerdown", () => cursor.classList.add("is-clicking"));
  window.addEventListener("pointerup", () => cursor.classList.remove("is-clicking"));
  document.documentElement.addEventListener("mouseleave", () => cursor.classList.remove("is-visible"));

  document.querySelectorAll("a, button, .assist-input-demo, .mini-card").forEach((target) => {
    target.addEventListener("mouseenter", () => cursor.classList.add("is-active"));
    target.addEventListener("mouseleave", () => cursor.classList.remove("is-active"));
  });
}

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

document.querySelectorAll("[data-assist-type-demo]").forEach((demo) => {
  const typed = demo.querySelector("[data-assist-typed]");
  const prompt = "Give me a softer ROI response for the price concern.";
  let index = 0;

  const runDemo = () => {
    index = 0;
    demo.classList.remove("is-typing");
    if (typed) {
      typed.textContent = "";
    }

    window.setTimeout(() => {
      demo.classList.add("is-typing");
      const typeInterval = window.setInterval(() => {
        if (!typed) {
          window.clearInterval(typeInterval);
          return;
        }

        typed.textContent = prompt.slice(0, index);
        index += 1;

        if (index > prompt.length) {
          window.clearInterval(typeInterval);
          window.setTimeout(() => demo.classList.remove("is-typing"), 1200);
        }
      }, 54);
    }, 2100);
  };

  runDemo();
  window.setInterval(runDemo, 7200);
});
