(function () {
  "use strict";

  var desktopMenus = Array.prototype.slice.call(document.querySelectorAll("[data-nav-menu]"));
  var mobileMenu = document.querySelector(".mobile-menu");
  var mobileToggle = document.querySelector(".mobile-menu__toggle");
  var mobilePanel = document.querySelector(".mobile-menu__panel");
  var mobileTriggers = Array.prototype.slice.call(document.querySelectorAll(".mobile-nav-group__trigger"));

  function setExpanded(button, panel, expanded) {
    button.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (panel) {
      panel.hidden = !expanded;
    }
  }

  function closeDesktopMenus(exceptMenu) {
    desktopMenus.forEach(function (menu) {
      if (menu === exceptMenu) {
        return;
      }
      var button = menu.querySelector(".nav-dropdown__trigger");
      var panel = menu.querySelector(".nav-dropdown__panel");
      if (button && panel) {
        setExpanded(button, panel, false);
      }
    });
  }

  desktopMenus.forEach(function (menu) {
    var button = menu.querySelector(".nav-dropdown__trigger");
    var panel = menu.querySelector(".nav-dropdown__panel");
    if (!button || !panel) {
      return;
    }
    button.addEventListener("click", function () {
      var willOpen = button.getAttribute("aria-expanded") !== "true";
      closeDesktopMenus(menu);
      setExpanded(button, panel, willOpen);
    });
    menu.addEventListener("mouseenter", function () {
      if (window.matchMedia("(hover: hover)").matches) {
        closeDesktopMenus(menu);
        setExpanded(button, panel, true);
      }
    });
    menu.addEventListener("mouseleave", function () {
      if (window.matchMedia("(hover: hover)").matches) {
        setExpanded(button, panel, false);
      }
    });
  });

  function openMobileMenu() {
    if (!mobileToggle || !mobilePanel) {
      return;
    }
    setExpanded(mobileToggle, mobilePanel, true);
    document.body.classList.add("nav-scroll-lock");
    var firstLink = mobilePanel.querySelector("a, button, input");
    if (firstLink) {
      firstLink.focus();
    }
  }

  function closeMobileMenu(restoreFocus) {
    if (!mobileToggle || !mobilePanel) {
      return;
    }
    setExpanded(mobileToggle, mobilePanel, false);
    document.body.classList.remove("nav-scroll-lock");
    if (restoreFocus) {
      mobileToggle.focus();
    }
  }

  if (mobileToggle && mobilePanel) {
    mobileToggle.addEventListener("click", function () {
      if (mobileToggle.getAttribute("aria-expanded") === "true") {
        closeMobileMenu(false);
      } else {
        openMobileMenu();
      }
    });
  }

  mobileTriggers.forEach(function (button) {
    var panel = document.getElementById(button.getAttribute("aria-controls"));
    if (!panel) {
      return;
    }
    if (button.dataset.current === "true") {
      setExpanded(button, panel, true);
    }
    button.addEventListener("click", function () {
      setExpanded(button, panel, button.getAttribute("aria-expanded") !== "true");
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-nav-menu]")) {
      closeDesktopMenus();
    }
    if (mobileMenu && !mobileMenu.contains(event.target) && mobileToggle && mobileToggle.getAttribute("aria-expanded") === "true") {
      closeMobileMenu(false);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") {
      return;
    }
    closeDesktopMenus();
    if (mobileToggle && mobileToggle.getAttribute("aria-expanded") === "true") {
      closeMobileMenu(true);
    }
  });
})();
