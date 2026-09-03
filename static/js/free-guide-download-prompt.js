(function () {
  "use strict";

  var modal = document.querySelector("[data-free-guide-download-modal]");
  if (!modal) {
    return;
  }

  var dialog = modal.querySelector(".free-guide-download-modal__dialog");
  var form = modal.querySelector(".newsletter-form");
  var email = form.querySelector('input[name="email"]');
  var pagePath = form.querySelector('input[name="page_path"]');
  var position = form.querySelector('input[name="analytics_position"]');
  var pendingDownload = null;
  var previousFocus = null;

  function isFreeGuideDownload(link) {
    if (!link || link.tagName !== "A") {
      return false;
    }
    if (link.hasAttribute("data-resource-download")) {
      return true;
    }
    try {
      return new URL(link.href, window.location.href).pathname.indexOf("/free-guides/pdfs/") !== -1;
    } catch (_error) {
      return false;
    }
  }

  function openModal(link) {
    pendingDownload = link;
    previousFocus = document.activeElement;
    if (pagePath) {
      pagePath.value = window.location.pathname || "/";
    }
    if (position) {
      position.value = link.dataset.trackPosition || "free-guide-download-prompt";
    }
    modal.hidden = false;
    document.body.classList.add("free-guide-download-modal-open");
    window.setTimeout(function () {
      email.focus();
    }, 0);
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove("free-guide-download-modal-open");
    if (previousFocus && typeof previousFocus.focus === "function") {
      previousFocus.focus();
    }
  }

  function startDownload() {
    if (!pendingDownload) {
      return;
    }
    var download = pendingDownload.cloneNode(true);
    download.setAttribute("data-free-guide-download-continue", "true");
    download.style.display = "none";
    document.body.appendChild(download);
    download.click();
    window.setTimeout(function () {
      download.remove();
    }, 0);
    pendingDownload = null;
  }

  document.addEventListener("click", function (event) {
    var link = event.target.closest("a");
    if (!isFreeGuideDownload(link) || link.hasAttribute("data-free-guide-download-continue")) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    openModal(link);
  }, true);

  modal.addEventListener("click", function (event) {
    if (event.target.closest("[data-free-guide-download-close]")) {
      closeModal();
      return;
    }
    if (event.target.closest("[data-free-guide-download-skip]")) {
      closeModal();
      startDownload();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });

  document.addEventListener("submit", function (event) {
    if (event.target !== form || event.defaultPrevented) {
      return;
    }
    closeModal();
    startDownload();
  });
})();
