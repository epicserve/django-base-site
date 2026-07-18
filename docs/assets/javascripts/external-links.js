// Open external docs links in a new tab. Pairs with the arrow icon added in
// assets/stylesheets/external-links.css.
document.addEventListener("DOMContentLoaded", () => {
  for (const link of document.querySelectorAll('.md-content a[href^="http"]')) {
    if (link.hostname !== window.location.hostname) {
      link.target = "_blank";
      link.rel = "noopener";
    }
  }
});
