(function () {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const revealElements = Array.from(document.querySelectorAll('.reveal'));
  if (revealElements.length) {
    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      revealElements.forEach((el) => el.classList.add('is-visible'));
    } else {
      const revealObserver = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) {
              return;
            }
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          });
        },
        { threshold: 0.16, rootMargin: '0px 0px -8% 0px' }
      );

      revealElements.forEach((el) => revealObserver.observe(el));
    }
  }

  const nav = document.querySelector('.navbar-custom');
  const updateNavState = () => {
    if (!nav) return;
    if (window.scrollY > 16) {
      nav.classList.add('is-scrolled');
    } else {
      nav.classList.remove('is-scrolled');
    }
  };
  updateNavState();
  window.addEventListener('scroll', updateNavState, { passive: true });

  if (!prefersReducedMotion) {
    const parallaxBg = document.querySelector('[data-parallax]');
    const parallaxCard = document.querySelector('[data-parallax-card]');

    const updateParallax = () => {
      if (!parallaxBg && !parallaxCard) return;
      const y = window.scrollY;

      if (parallaxBg) {
        parallaxBg.style.transform = `translate3d(0, ${y * -0.08}px, 0) scale(1.03)`;
      }

      if (parallaxCard) {
        parallaxCard.style.transform = `translate3d(0, ${y * -0.03}px, 0)`;
      }
    };

    updateParallax();
    window.addEventListener('scroll', updateParallax, { passive: true });
  }
})();
