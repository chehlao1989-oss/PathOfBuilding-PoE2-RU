'use strict';

(() => {
  // Replace only with the GA4 web-stream ID owned by the project author.
  const measurementId = 'G-RJD35VBT5C';
  const host = 'chehlao1989-oss.github.io';
  const path = '/PathOfBuilding-PoE2-RU/';
  const location = window.location;
  if (!/^G-[A-Z0-9]+$/.test(measurementId)) return;
  if (location.protocol !== 'https:' || location.hostname !== host || !location.pathname.startsWith(path)) return;
  const query = new URLSearchParams(location.search);
  const optOutKey = 'pob2ru.analytics.disabled';
  let optedOut = query.get('analytics') === 'off';
  try {
    if (optedOut) window.localStorage.setItem(optOutKey, '1');
    else if (query.get('analytics') === 'on') window.localStorage.removeItem(optOutKey);
    optedOut = optedOut || window.localStorage.getItem(optOutKey) === '1';
  } catch {
    // The explicit URL opt-out still works when browser storage is unavailable.
  }
  if (optedOut) {
    window['ga-disable-' + measurementId] = true;
    return;
  }
  if (window['ga-disable-' + measurementId]) return;
  if (window.__pob2ruAnalyticsInitialized) return;
  window.__pob2ruAnalyticsInitialized = true;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  const config = {
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  };
  if (query.get('analytics_debug') === '1') config.debug_mode = true;
  window.gtag('config', measurementId, config);

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(measurementId);
  document.head.appendChild(script);

  document.addEventListener('click', event => {
    if (event.button !== 0 || event.defaultPrevented) return;
    const link = event.target instanceof Element ? event.target.closest('a.download-link') : null;
    if (!link) return;
    let url;
    try {
      url = new URL(link.href);
    } catch {
      return;
    }
    if (url.origin !== 'https://github.com' ||
        !url.pathname.startsWith('/chehlao1989-oss/PathOfBuilding-PoE2-RU/releases/download/') ||
        !url.pathname.endsWith('.zip')) return;
    const button = link.closest('.hero') ? 'hero' : link.closest('.download-section') ? 'footer' : 'other';
    const filename = url.pathname.split('/').pop();
    try {
      window.gtag('event', 'download_click', {
        send_to: measurementId,
        button_position: button,
        file_name: filename,
        file_extension: 'zip',
        link_url: url.href,
        transport_type: 'beacon'
      });
    } catch {
      // A blocked counter must never stop the normal archive link.
    }
  });
})();
