(function () {
  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
      return;
    }
    callback();
  }

  function mix(start, end, amount) {
    return Math.round(start + (end - start) * amount);
  }

  function rgb(color) {
    return "rgb(" + color.join(", ") + ")";
  }

  ready(function () {
    var details = Array.prototype.slice.call(document.querySelectorAll(".mobile-blog-subscribe__details"));
    var triggers = Array.prototype.slice.call(document.querySelectorAll(".mobile-blog-subscribe__trigger"));
    var green = [0, 80, 48];
    var orange = [240, 114, 57];
    var pendingFrame = false;

    if (!details.length) {
      return;
    }

    function closeOpenDetails(event) {
      details.forEach(function (item) {
        if (item.open && !item.contains(event.target)) {
          item.open = false;
        }
      });
    }

    function closeOnEscape(event) {
      if (event.key !== "Escape") {
        return;
      }
      details.forEach(function (item) {
        item.open = false;
      });
    }

    function paintTriggers() {
      var wave = (Math.sin(window.scrollY / 260) + 1) / 2;
      var colorA = [
        mix(green[0], orange[0], wave),
        mix(green[1], orange[1], wave),
        mix(green[2], orange[2], wave),
      ];
      var colorB = [
        mix(orange[0], green[0], wave),
        mix(orange[1], green[1], wave),
        mix(orange[2], green[2], wave),
      ];
      var glowColor = [
        mix(0, 240, wave),
        mix(80, 114, wave),
        mix(48, 57, wave),
      ];
      var position = Math.round(20 + wave * 60) + "% 50%";

      triggers.forEach(function (trigger) {
        trigger.style.setProperty("--mobile-blog-subscribe-color-a", rgb(colorA));
        trigger.style.setProperty("--mobile-blog-subscribe-color-b", rgb(colorB));
        trigger.style.setProperty("--mobile-blog-subscribe-glow", "rgba(" + glowColor.join(", ") + ", 0.3)");
        trigger.style.setProperty("--mobile-blog-subscribe-bg-position", position);
      });
      pendingFrame = false;
    }

    function requestPaint() {
      if (pendingFrame) {
        return;
      }
      pendingFrame = true;
      window.requestAnimationFrame(paintTriggers);
    }

    document.addEventListener("pointerdown", closeOpenDetails);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("scroll", requestPaint, { passive: true });
    paintTriggers();
  });
})();
