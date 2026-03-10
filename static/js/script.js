(function () {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const allowTilt = !reduceMotion && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  const revealTargets = document.querySelectorAll('.reveal-on-scroll');
  if (revealTargets.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealTargets.forEach((node) => node.classList.add('is-visible'));
    } else {
      const observer = new IntersectionObserver(
        (entries, obs) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('is-visible');
            obs.unobserve(entry.target);
          });
        },
        { threshold: 0.14, rootMargin: '0px 0px -6% 0px' }
      );

      revealTargets.forEach((node) => observer.observe(node));
    }
  }

  const nav = document.querySelector('.navbar-custom');
  const updateNav = () => {
    if (!nav) return;
    nav.classList.toggle('is-scrolled', window.scrollY > 16);
  };
  updateNav();
  window.addEventListener('scroll', updateNav, { passive: true });

  if (!reduceMotion) {
    const hero = document.querySelector('.f66-hero');
    const heroGlow = document.querySelector('.f66-hero-glow');
    let parallaxScheduled = false;

    const updateParallax = () => {
      if (!hero || !heroGlow) return;
      const rect = hero.getBoundingClientRect();
      const progress = Math.max(-1, Math.min(1, rect.top / window.innerHeight));
      const y = progress * -28;
      heroGlow.style.transform = `translate3d(0, ${y}px, 0)`;
      parallaxScheduled = false;
    };

    updateParallax();
    window.addEventListener('scroll', () => {
      if (parallaxScheduled) return;
      parallaxScheduled = true;
      requestAnimationFrame(updateParallax);
    }, { passive: true });

    if (allowTilt) {
      const tiltCards = document.querySelectorAll('[data-tilt-card]');
      tiltCards.forEach((card) => {
        card.addEventListener('mousemove', (event) => {
          const r = card.getBoundingClientRect();
          const x = (event.clientX - r.left) / r.width;
          const y = (event.clientY - r.top) / r.height;

          const rotateY = (x - 0.5) * 7;
          const rotateX = (0.5 - y) * 7;
          card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
          card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
        });
      });
    }
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  const csrfToken =
    getCookie('csrftoken') ||
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
    document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
    '';
  const reactionRows = document.querySelectorAll('.reaction-row[data-post-id]');

  const passwordToggles = document.querySelectorAll('[data-password-toggle]');
  passwordToggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      const targetId = toggle.getAttribute('data-target');
      const input = targetId ? document.getElementById(targetId) : null;
      if (!input) return;
      const nextType = input.type === 'password' ? 'text' : 'password';
      input.type = nextType;
      toggle.textContent = nextType === 'password' ? 'Показать' : 'Скрыть';
      toggle.setAttribute('aria-pressed', nextType === 'text' ? 'true' : 'false');
    });
  });

  reactionRows.forEach((row) => {
    const postId = row.dataset.postId;
    const buttons = row.querySelectorAll('[data-react-btn]');
    const likeCounter = row.querySelector('[data-like-count]');
    const dislikeCounter = row.querySelector('[data-dislike-count]');

    buttons.forEach((button) => {
      button.addEventListener('click', async (event) => {
        event.preventDefault();
        if (row.dataset.pending === 'true') return;
        const reactionType = button.dataset.reaction;
        row.dataset.pending = 'true';
        row.setAttribute('aria-busy', 'true');
        buttons.forEach((item) => { item.disabled = true; });

        try {
          const response = await fetch(`/posts/${postId}/react/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'Accept': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
              'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            },
            body: new URLSearchParams({ reaction_type: reactionType }),
          });

          if (response.status === 401) {
            const data = await response.json().catch(() => null);
            if (data?.login_url) {
              window.location.href = data.login_url;
            }
            return;
          }

          if (!response.ok) {
            return;
          }

          const data = await response.json();
          if (!data.ok) {
            return;
          }

          buttons.forEach((item) => {
            item.classList.remove('is-active');
            item.setAttribute('aria-pressed', 'false');
          });
          const activeBtn = row.querySelector(`[data-reaction="${data.reaction}"]`);
          if (activeBtn) {
            activeBtn.classList.add('is-active');
            activeBtn.setAttribute('aria-pressed', 'true');
            activeBtn.classList.remove('pulse');
            requestAnimationFrame(() => activeBtn.classList.add('pulse'));
          }

          if (likeCounter) likeCounter.textContent = data.likes_count;
          if (dislikeCounter) dislikeCounter.textContent = data.dislikes_count;
        } catch (error) {
          // ignore network errors on client side
        } finally {
          row.dataset.pending = 'false';
          row.setAttribute('aria-busy', 'false');
          buttons.forEach((item) => { item.disabled = false; });
        }
      });
    });
  });
})();
