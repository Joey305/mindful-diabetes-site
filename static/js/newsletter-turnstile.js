(function () {
  function submitButtonFor(form) {
    return form.querySelector('button[type="submit"]');
  }

  function setButtonState(form, isChecking) {
    const button = submitButtonFor(form);
    if (!button) {
      return;
    }

    if (isChecking) {
      button.dataset.originalText = button.textContent;
      button.textContent = "Checking...";
      button.disabled = true;
      return;
    }

    button.textContent = button.dataset.originalText || "Subscribe";
    button.disabled = false;
    delete button.dataset.originalText;
  }

  function pendingForm() {
    return document.querySelector('.newsletter-form[data-turnstile-pending="true"]');
  }

  function turnstileTokenFor(form) {
    const field = form.querySelector('input[name="cf-turnstile-response"]');
    return field ? field.value : "";
  }

  function setTurnstileToken(form, token) {
    let field = form.querySelector('input[name="cf-turnstile-response"]');
    if (!field) {
      field = document.createElement("input");
      field.type = "hidden";
      field.name = "cf-turnstile-response";
      form.appendChild(field);
    }
    field.value = token;
  }

  window.onNewsletterTurnstileSuccess = function (token) {
    const form = pendingForm();
    if (!form) {
      return;
    }

    setTurnstileToken(form, token);
    delete form.dataset.turnstilePending;
    setButtonState(form, false);
    form.requestSubmit();
  };

  window.onNewsletterTurnstileError = function () {
    const form = pendingForm();
    if (!form) {
      return;
    }

    delete form.dataset.turnstilePending;
    setButtonState(form, false);
  };

  window.onNewsletterTurnstileExpired = function () {
    const form = pendingForm();
    if (!form || !window.turnstile) {
      return;
    }

    window.turnstile.reset(form.querySelector(".newsletter-form__turnstile"));
  };

  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!form.matches(".newsletter-form")) {
      return;
    }

    const widget = form.querySelector(".newsletter-form__turnstile");
    if (!widget || turnstileTokenFor(form)) {
      return;
    }

    event.preventDefault();

    if (!window.turnstile) {
      setButtonState(form, true);
      window.setTimeout(function () {
        setButtonState(form, false);
      }, 800);
      return;
    }

    document.querySelectorAll(".newsletter-form").forEach(function (otherForm) {
      delete otherForm.dataset.turnstilePending;
      if (otherForm !== form) {
        setButtonState(otherForm, false);
      }
    });

    form.dataset.turnstilePending = "true";
    setButtonState(form, true);
    window.turnstile.execute(widget);
  });
})();
