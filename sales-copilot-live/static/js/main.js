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
