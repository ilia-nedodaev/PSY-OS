function saveAuthFromResponse(data) {
  Auth.save({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    role: data.role,
    locale: data.locale,
  });
  Auth.setLocale(data.locale || 'uk');
}

function showFormError(form, field, message) {
  const errorEl = form.querySelector(`.form-error[data-for="${field}"]`);
  const inputEl = form.querySelector(`[name="${field}"], #${field}`);
  if (errorEl) errorEl.textContent = message;
  if (inputEl) inputEl.classList.add('error');
}

function clearFormErrors(form) {
  form.querySelectorAll('.form-error').forEach(el => { el.textContent = ''; });
  form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
}

function initPasswordToggles(root = document) {
  root.querySelectorAll('.password-toggle').forEach(toggle => {
    const input = toggle.closest('.password-input')?.querySelector('input');
    if (!input) return;
    toggle.addEventListener('click', () => {
      const hidden = input.type === 'password';
      input.type = hidden ? 'text' : 'password';
      toggle.classList.toggle('is-visible', hidden);
    });
  });
}

function initPsychologistRegister() {
  const form = document.getElementById('registerForm');
  if (!form) return;

  initPasswordToggles(form);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors(form);

    const password = form.password.value;
    if (password !== form.confirmPassword.value) {
      showFormError(form, 'confirmPassword', 'Паролі не співпадають');
      return;
    }
    if (!form.terms.checked) {
      showFormError(form, 'terms', 'Потрібна згода');
      return;
    }

    try {
      const data = await API.registerPsychologist({
        first_name: form.firstName.value.trim(),
        last_name: form.lastName.value.trim(),
        email: form.email.value.trim(),
        phone: form.phone.value.trim() || null,
        password,
        locale: Auth.locale(),
      });
      saveAuthFromResponse(data);
      window.location.href = 'psychologist-dashboard.html';
    } catch (err) {
      const msg = typeof err.data?.detail === 'string' ? err.data.detail : 'Помилка реєстрації';
      showFormError(form, 'email', msg);
    }
  });
}

function initPsychologistLogin() {
  const form = document.getElementById('psychologistLoginForm');
  if (!form) return;

  initPasswordToggles(form);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors(form);
    try {
      const data = await API.loginPsychologist(form.email.value.trim(), form.password.value);
      saveAuthFromResponse(data);
      window.location.href = 'psychologist-dashboard.html';
    } catch {
      showFormError(form, 'password', 'Невірний email або пароль');
    }
  });
}

function initClientLogin() {
  const form = document.getElementById('clientLoginForm');
  if (!form) return;

  initPasswordToggles(form);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearFormErrors(form);
    try {
      const data = await API.loginClient(form.username.value.trim(), form.password.value);
      saveAuthFromResponse(data);
      window.location.href = 'client-dashboard.html';
    } catch {
      showFormError(form, 'password', 'Невірний логін або пароль');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initPsychologistRegister();
  initPsychologistLogin();
  initClientLogin();
});
