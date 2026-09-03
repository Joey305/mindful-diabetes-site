(function () {
  "use strict";

  function showConfirmation(message) {
    var confirmation = document.querySelector(".free-guides-confirmation");
    if (!confirmation) {
      return;
    }
    confirmation.textContent = message;
    confirmation.hidden = false;
    window.clearTimeout(showConfirmation.timer);
    showConfirmation.timer = window.setTimeout(function () {
      confirmation.hidden = true;
    }, 4200);
  }

  document.addEventListener("click", function (event) {
    var copyButton = event.target.closest("[data-copy-resource-link]");
    if (!copyButton) {
      return;
    }
    var link = copyButton.dataset.copyResourceLink;
    if (!link) {
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(link).then(function () {
        showConfirmation("Guide link copied.");
      }).catch(function () {
        showConfirmation(link);
      });
    } else {
      showConfirmation(link);
    }
  });
})();
