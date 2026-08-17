document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initRegisterForm();
  initLoginForm();
});

function initMobileNav() {
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (!toggle || !navLinks) return;

  toggle.addEventListener('click', () => {
    const isOpen = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!isOpen));
    navLinks.classList.toggle('open');
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      toggle.setAttribute('aria-expanded', 'false');
      navLinks.classList.remove('open');
    });
  });
}

function initPasswordToggle(form) {
  const passwordToggle = form.querySelector('.password-toggle');
  const passwordInput = form.querySelector('#password');

  if (!passwordToggle || !passwordInput) return;

  passwordToggle.addEventListener('click', () => {
    const isHidden = passwordInput.type === 'password';
    passwordInput.type = isHidden ? 'text' : 'password';
    passwordToggle.classList.toggle('is-visible', isHidden);
    passwordToggle.setAttribute('aria-label', isHidden ? 'Приховати пароль' : 'Показати пароль');
  });
}

function initRegisterForm() {
  const form = document.getElementById('registerForm');
  if (!form) return;

  initPasswordToggle(form);
  const successBlock = document.getElementById('registerSuccess');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearErrors(form);

    const data = new FormData(form);
    const errors = validateForm(data);

    if (Object.keys(errors).length > 0) {
      showErrors(form, errors);
      return;
    }

    form.hidden = true;
    if (successBlock) {
      successBlock.hidden = false;
    }
  });
}

function initLoginForm() {
  document.querySelectorAll('[data-login-type]').forEach((form) => {
    initPasswordToggle(form);
    const successBlock = form.parentElement.querySelector('.register-success');

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      clearErrors(form);

      const data = new FormData(form);
      const errors = validateLoginForm(data, form.dataset.loginType);

      if (Object.keys(errors).length > 0) {
        showErrors(form, errors);
        return;
      }

      form.hidden = true;
      if (successBlock) {
        successBlock.hidden = false;
      }
    });
  });
}

function validateLoginForm(data, loginType) {
  const errors = {};
  const password = data.get('password') || '';

  if (loginType === 'client') {
    const username = (data.get('username') || '').trim();

    if (!username) {
      errors.username = 'Введіть логін';
    } else if (username.length < 3) {
      errors.username = 'Логін має містити мінімум 3 символи';
    }
  } else {
    const email = (data.get('email') || '').trim();

    if (!email) {
      errors.email = 'Введіть електронну пошту';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Невірний формат електронної пошти';
    }
  }

  if (!password) {
    errors.password = 'Введіть пароль';
  }

  return errors;
}

function validateForm(data) {
  const errors = {};

  const firstName = (data.get('firstName') || '').trim();
  const lastName = (data.get('lastName') || '').trim();
  const email = (data.get('email') || '').trim();
  const password = data.get('password') || '';
  const confirmPassword = data.get('confirmPassword') || '';
  const terms = data.get('terms');

  if (!firstName) {
    errors.firstName = "Введіть ім'я";
  }

  if (!lastName) {
    errors.lastName = 'Введіть прізвище';
  }

  if (!email) {
    errors.email = 'Введіть електронну пошту';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = 'Невірний формат електронної пошти';
  }

  if (!password) {
    errors.password = 'Введіть пароль';
  } else if (password.length < 8) {
    errors.password = 'Пароль має містити мінімум 8 символів';
  }

  if (password !== confirmPassword) {
    errors.confirmPassword = 'Паролі не співпадають';
  }

  if (!terms) {
    errors.terms = 'Необхідно погодитись з умовами';
  }

  return errors;
}

function clearErrors(form) {
  form.querySelectorAll('.form-error').forEach(el => {
    el.textContent = '';
  });
  form.querySelectorAll('.error').forEach(el => {
    el.classList.remove('error');
  });
}

function showErrors(form, errors) {
  Object.entries(errors).forEach(([field, message]) => {
    const errorEl = form.querySelector(`.form-error[data-for="${field}"]`);
    const inputEl = form.querySelector(`[name="${field}"], #${field}`);

    if (errorEl) {
      errorEl.textContent = message;
    }
    if (inputEl) {
      inputEl.classList.add('error');
    }
  });
}
