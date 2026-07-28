(function () {
  "use strict";

  if (window.__mdiAnalyticsLoaded) {
    return;
  }
  window.__mdiAnalyticsLoaded = true;

  var scriptConfig = document.currentScript ? document.currentScript.dataset : {};
  var config = window.__MDI_ANALYTICS__ || {
    enabled: scriptConfig.enabled === "1",
    endpoint: scriptConfig.endpoint || "",
    environment: scriptConfig.environment || "",
  };
  if (!config.enabled || !config.endpoint) {
    return;
  }

  var sentPageView = false;
  var recentClicks = new Set();
  var impressed = new WeakSet();

  function sessionId() {
    try {
      var key = "mdi_analytics_session_id";
      var existing = window.sessionStorage.getItem(key);
      if (existing) {
        return existing;
      }
      var generated = "sess_" + randomId();
      window.sessionStorage.setItem(key, generated);
      return generated;
    } catch (_error) {
      return "sess_" + randomId();
    }
  }

  function randomId() {
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function deviceCategory() {
    var width = window.innerWidth || document.documentElement.clientWidth || 1200;
    if (width < 760) {
      return "mobile";
    }
    if (width < 1100) {
      return "tablet";
    }
    return "desktop";
  }

  function utmParams() {
    var params = new URLSearchParams(window.location.search);
    return {
      source: params.get("utm_source") || "",
      medium: params.get("utm_medium") || "",
      campaign: params.get("utm_campaign") || "",
      term: params.get("utm_term") || "",
      campaign_content: params.get("utm_content") || "",
    };
  }

  function domainFor(url) {
    try {
      return url ? new URL(url, window.location.href).hostname : "";
    } catch (_error) {
      return "";
    }
  }

  function absoluteUrl(url) {
    if (!url) {
      return "";
    }
    try {
      return new URL(url, window.location.href).toString();
    } catch (_error) {
      return url;
    }
  }

  function baseEvent() {
    var utm = utmParams();
    return {
      event_id: "client:" + randomId(),
      schema_version: 1,
      client_occurred_at: new Date().toISOString(),
      page_path: window.location.pathname || "/",
      page_title: document.title || "",
      referrer_url: document.referrer || "",
      referrer_domain: domainFor(document.referrer),
      anonymous_session_id: sessionId(),
      device_category: deviceCategory(),
      environment: config.environment || "",
      source: utm.source,
      medium: utm.medium,
      campaign: utm.campaign,
      term: utm.term,
      campaign_content: utm.campaign_content,
      metadata: {},
    };
  }

  function metadataFrom(element) {
    var allowed = [
      "campaignId",
      "campaignName",
      "donationKind",
      "frequency",
      "provider",
      "toolId",
      "toolName",
      "toolSlug",
      "toolDestinationType",
      "signupFormId",
      "blockPosition",
      "attributionSource",
      "relatedArticle",
      "resourceId",
      "resourceType",
      "sponsorId",
      "eventId",
      "volunteerRole",
      "linkKind",
    ];
    var keyMap = {
      campaignId: "campaign_id",
      campaignName: "campaign_name",
      donationKind: "donation_kind",
      frequency: "frequency",
      provider: "provider",
      toolId: "tool_id",
      toolName: "tool_name",
      toolSlug: "tool_slug",
      toolDestinationType: "tool_destination_type",
      signupFormId: "signup_form_id",
      blockPosition: "block_position",
      attributionSource: "attribution_source",
      relatedArticle: "related_article",
      resourceId: "resource_id",
      resourceType: "resource_type",
      sponsorId: "sponsor_id",
      eventId: "event_id",
      volunteerRole: "volunteer_role",
      linkKind: "link_kind",
    };
    var metadata = {};
    allowed.forEach(function (name) {
      var value = element.dataset[name];
      if (value) {
        metadata[keyMap[name]] = value;
      }
    });
    return metadata;
  }

  function eventFromElement(element, eventName) {
    var base = baseEvent();
    var destination = element.dataset.trackDestination || element.getAttribute("href") || element.getAttribute("action") || "";
    var event = Object.assign(base, {
      event_name: eventName,
      event_category: element.dataset.trackCategory || "",
      content_id: element.dataset.trackContentId || "",
      content_type: element.dataset.trackContentType || "",
      article_group: element.dataset.trackArticleGroup || "",
      element_id: element.dataset.trackId || element.id || "",
      element_label: element.dataset.trackLabel || element.getAttribute("aria-label") || element.textContent.trim().slice(0, 120),
      element_type: element.dataset.trackElementType || element.tagName.toLowerCase(),
      element_position: element.dataset.trackPosition || "",
      destination_url: absoluteUrl(destination),
      destination_domain: domainFor(destination),
      campaign: element.dataset.trackCampaignId || base.campaign,
      metadata: metadataFrom(element),
    });
    return event;
  }

  function send(event) {
    var body = JSON.stringify(event);
    try {
      if (navigator.sendBeacon) {
        var blob = new Blob([body], { type: "application/json" });
        if (navigator.sendBeacon(config.endpoint, blob)) {
          return;
        }
      }
      window.fetch(config.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
        credentials: "same-origin",
        keepalive: true,
      }).catch(function () {});
    } catch (_error) {}
  }

  function trackPageView() {
    if (sentPageView) {
      return;
    }
    sentPageView = true;
    var event = baseEvent();
    event.event_name = "page_view";
    event.event_category = "content";
    send(event);
  }

  function trackClick(event) {
    var target = event.target.closest("[data-track-event]");
    if (!target) {
      return;
    }
    var eventName = target.dataset.trackEvent;
    if (!eventName) {
      return;
    }
    var dedupeKey = (target.dataset.trackId || target.href || target.textContent || eventName) + ":" + eventName;
    if (recentClicks.has(dedupeKey)) {
      return;
    }
    recentClicks.add(dedupeKey);
    window.setTimeout(function () {
      recentClicks.delete(dedupeKey);
    }, 900);
    send(eventFromElement(target, eventName));
  }

  function initImpressions() {
    if (!("IntersectionObserver" in window)) {
      return;
    }
    var timers = new WeakMap();
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          var element = entry.target;
          if (impressed.has(element)) {
            return;
          }
          if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
            if (!timers.has(element)) {
              timers.set(
                element,
                window.setTimeout(function () {
                  impressed.add(element);
                  send(eventFromElement(element, "cta_impression"));
                  observer.unobserve(element);
                }, 1000)
              );
            }
          } else if (timers.has(element)) {
            window.clearTimeout(timers.get(element));
            timers.delete(element);
          }
        });
      },
      { threshold: [0.5] }
    );
    document.querySelectorAll("[data-track-impression]").forEach(function (element) {
      observer.observe(element);
    });
  }

  function copySessionToNewsletterForms() {
    document.querySelectorAll(".newsletter-form").forEach(function (form) {
      var sessionInput = form.querySelector("input[name='analytics_session_id']");
      if (sessionInput) {
        sessionInput.value = sessionId();
      }
      var pageInput = form.querySelector("input[name='page_path']");
      if (pageInput) {
        pageInput.value = window.location.pathname || "/";
      }
    });
  }

  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) {
      trackPageView();
    }
  });
  document.addEventListener("click", trackClick, true);
  document.addEventListener("focusin", function (event) {
    var form = event.target.closest(".newsletter-form[data-track-event]");
    if (form && !form.dataset.analyticsInteracted) {
      form.dataset.analyticsInteracted = "1";
      send(eventFromElement(form, "newsletter_form_interaction"));
    }
  });
  document.addEventListener("DOMContentLoaded", function () {
    copySessionToNewsletterForms();
    initImpressions();
  });
})();
