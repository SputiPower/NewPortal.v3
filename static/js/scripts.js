document.addEventListener("DOMContentLoaded", () => {

  // ==== 1. Показ/скрытие пароля ====
  const togglePasswordBtn = document.querySelector(".show-password");
  if (togglePasswordBtn) {
    togglePasswordBtn.addEventListener("click", () => {
      const input = document.querySelector('input[type="password"], input[type="text"]');
      if (!input) return;
      if (input.type === "password") {
        input.type = "text";
        togglePasswordBtn.textContent = "🙈 Скрыть";
      } else {
        input.type = "password";
        togglePasswordBtn.textContent = "👁 Показать";
      }
    });
  }

  // ==== 2. Анимация кнопки отправки ====
  const submitBtn = document.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.addEventListener("mouseenter", () => {
      submitBtn.style.transform = "scale(1.05)";
      submitBtn.style.boxShadow = "0 10px 25px rgba(76, 175, 80, 0.6)";
    });
    submitBtn.addEventListener("mouseleave", () => {
      submitBtn.style.transform = "scale(1)";
      submitBtn.style.boxShadow = "0 5px 15px rgba(56, 142, 60, 0.5)";
    });
  }

  // ==== 3. Подсветка полей при фокусе ====
  const inputs = document.querySelectorAll(".input-wrapper input");
  inputs.forEach(input => {
    input.addEventListener("focus", () => {
      input.style.borderColor = "#4caf50";
      input.style.boxShadow = "0 0 10px rgba(76, 175, 80, 0.3)";
    });
    input.addEventListener("blur", () => {
      input.style.borderColor = "";
      input.style.boxShadow = "";
    });
  });

  // ==== 4. Анимация социальных кнопок ====
  const socialButtons = document.querySelectorAll(".google-btn, .yandex-btn");
  socialButtons.forEach(btn => {
    btn.addEventListener("mouseenter", () => {
      btn.style.transform = "translateY(-3px) scale(1.02)";
      btn.style.boxShadow = "0 8px 20px rgba(0,0,0,0.25)";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "translateY(0) scale(1)";
      btn.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
    });
  });

  // ==== 5. Плавное появление формы при загрузке страницы ====
  const formWrapper = document.querySelector(".form-wrapper");
  if (formWrapper) {
    formWrapper.style.opacity = 0;
    formWrapper.style.transform = "translateY(30px)";
    formWrapper.style.transition = "opacity 0.8s ease, transform 0.8s ease";
    requestAnimationFrame(() => {
      formWrapper.style.opacity = 1;
      formWrapper.style.transform = "translateY(0)";
    });
  }

  // ==== 6. Лёгкая анимация при ошибках формы ====
  const errorBoxes = document.querySelectorAll(".non-field-errors, .error-message");
  errorBoxes.forEach(box => {
    box.style.opacity = 0;
    box.style.transform = "translateY(-10px)";
    box.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    requestAnimationFrame(() => {
      box.style.opacity = 1;
      box.style.transform = "translateY(0)";
    });
  });

});

// Анимация плавного появления формы
document.addEventListener('DOMContentLoaded', () => {
  const formWrapper = document.querySelector('.form-wrapper');
  if (formWrapper) {
    formWrapper.style.opacity = 0;
    formWrapper.style.transition = 'opacity 1s ease-in-out';
    setTimeout(() => {
      formWrapper.style.opacity = 1;
    }, 100);
  }

  // Добавим анимацию при наведении на соцкнопки
  const socialButtons = document.querySelectorAll('.google-btn, .yandex-btn');
  socialButtons.forEach(btn => {
    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'scale(1.05)';
      btn.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'scale(1)';
      btn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
    });
  });
});

