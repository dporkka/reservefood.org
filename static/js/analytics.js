(function () {
  var script = document.currentScript;
  var domain = script ? script.getAttribute("data-domain") : "";

  var dnt = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack;
  if (!domain || dnt === "1" || dnt === "yes") return;

  var payload = {
    name: "pageview",
    url: window.location.href,
    domain: domain
  };

  var body = new Blob([JSON.stringify(payload)], { type: "application/json" });
  if (navigator.sendBeacon && navigator.sendBeacon(
    "https://plausible.io/api/event",
    body
  )) return;

  fetch("https://plausible.io/api/event", {
    method: "POST",
    body: body,
    keepalive: true,
    headers: { "Content-Type": "application/json" }
  }).catch(function () {});
})();
