(function () {
  var root = document.documentElement;
  var header = document.querySelector(".site-header");
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var desktop = window.matchMedia("(min-width: 801px)");

  // Mobile menu ---------------------------------------------------------------
  var btn = header && header.querySelector(".menu-btn");

  // While the menu covers the page, the page behind it is inert: keyboard
  // focus and screen readers stay in the menu (WCAG 2.4.11)
  var behindMenu = document.querySelectorAll(".skip, main, .site-footer");

  function setMenu(open) {
    header.classList.toggle("is-open", open);
    root.classList.toggle("menu-open", open);
    behindMenu.forEach(function (el) { el.inert = open; });
    btn.setAttribute("aria-expanded", String(open));
    var label = btn.querySelector(".sr");
    if (label) label.textContent = open ? "Close menu" : "Menu";
    if (open) setHeaderHidden(false);
  }

  if (btn) {
    btn.addEventListener("click", function () {
      setMenu(!header.classList.contains("is-open"));
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setMenu(false);
    });
    desktop.addEventListener("change", function (e) {
      if (e.matches) setMenu(false);
    });
  }

  // Menu bar (desktop): one bar glides to the item under the pointer and back
  // to the current page's item when the pointer leaves ----------------------
  var nav = header && header.querySelector(".nav");
  if (nav) {
    var bar = document.createElement("span");
    bar.className = "nav__bar";
    bar.setAttribute("aria-hidden", "true");
    nav.appendChild(bar);
    nav.classList.add("has-bar");
    var current = nav.querySelector(":scope > a[aria-current]");
    var barX = 0, barW = 0;
    var placeBar = function (a, instant) {
      var x = a ? a.offsetLeft : barX + barW; // no target: shrink away to the right
      var w = a ? a.offsetWidth : 0;
      if (a && !barW) {
        // appearing: start as a zero-width bar at the item's left edge
        bar.style.transition = "none";
        bar.style.transform = "translateX(" + x + "px)";
        bar.style.width = "0px";
        bar.getBoundingClientRect();
      }
      bar.style.transition = instant ? "none" : "";
      bar.style.transform = "translateX(" + x + "px)";
      bar.style.width = w + "px";
      barX = x;
      barW = w;
    };
    placeBar(current, true);
    nav.querySelectorAll(":scope > a").forEach(function (a) {
      // the white CV block doesn't take the bar
      var target = a.classList.contains("nav__cv") ? null : a;
      a.addEventListener("pointerenter", function () { placeBar(target || current); });
      a.addEventListener("focus", function () { placeBar(target || current); });
    });
    nav.addEventListener("pointerleave", function () { placeBar(current); });
    nav.addEventListener("focusout", function (e) {
      if (!nav.contains(e.relatedTarget)) placeBar(current);
    });
    window.addEventListener("resize", function () { placeBar(current, true); });
    // the header's own font may settle after first paint
    if (document.fonts) document.fonts.ready.then(function () { placeBar(current, true); });
  }

  // Header: hides while scrolling down, returns when scrolling up; progress line
  function setHeaderHidden(hidden) {
    if (!header || header.classList.contains("is-hidden") === hidden) return;
    header.classList.toggle("is-hidden", hidden);
  }

  if (header) {
    var progress = header.querySelector(".progress");
    var lastY = window.scrollY;
    var ticking = false;
    var maxScroll = 0;

    // Page height only changes on resize or when content loads, so measure it
    // then rather than on every scroll frame.
    var measure = function () {
      maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    };
    measure();
    window.addEventListener("resize", measure);
    if ("ResizeObserver" in window) new ResizeObserver(measure).observe(document.body);

    var onScroll = function () {
      ticking = false;
      var y = window.scrollY;
      if (progress) {
        var p = maxScroll > 0 ? Math.min(1, Math.max(0, y / maxScroll)) : 0;
        progress.style.transform = "scaleX(" + p.toFixed(4) + ")";
      }

      var busy = header.classList.contains("is-open") || header.contains(document.activeElement);
      if (y < 200 || y < lastY - 6) setHeaderHidden(false);
      else if (y > lastY + 6 && !busy) setHeaderHidden(true);
      lastY = y;
    };

    window.addEventListener("scroll", function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(onScroll);
      }
    }, { passive: true });
    header.addEventListener("focusin", function () { setHeaderHidden(false); });
    onScroll();
  }

  // Scroll reveals ------------------------------------------------------------
  // Elements marked data-draw (grid lines) or data-reveal (text, images) get
  // .is-in once they scroll into view. CSS does the animating.
  var targets = document.querySelectorAll("[data-draw], [data-reveal]");

  if (reduced || !("IntersectionObserver" in window)) {
    targets.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px" });

    targets.forEach(function (el) { io.observe(el); });
  }

  root.classList.add("reveal-ready");

  // Anything that receives keyboard focus is shown at once, so focus never
  // lands on content that's still faded out
  document.addEventListener("focusin", function (e) {
    for (var el = e.target; el && el !== document.body; el = el.parentElement) {
      if (el.hasAttribute("data-reveal") || el.hasAttribute("data-draw")) el.classList.add("is-in");
    }
  });

  // Escape hides hover extras (card info panel, "Enlarge" badge) without
  // moving the pointer; they come back on the next hover or focus (WCAG 1.4.13)
  // Hiding the panel changes what's under a still pointer, so only a real
  // pointer movement (or moving focus) brings the extras back.
  var px = 0, py = 0, offX = 0, offY = 0;
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    root.classList.add("hover-off");
    offX = px; offY = py;
  });
  document.addEventListener("pointermove", function (e) {
    px = e.clientX; py = e.clientY;
    if (root.classList.contains("hover-off") && Math.abs(px - offX) + Math.abs(py - offY) > 8) {
      root.classList.remove("hover-off");
    }
  }, { passive: true });
  document.addEventListener("focusin", function () { root.classList.remove("hover-off"); });

  // Page transitions ------------------------------------------------------------
  // The head script marks html.arriving when this page was entered through a
  // view transition, so what's on screen appears as part of that one motion.
  // Once it ends, everything visible counts as revealed (nothing fades back
  // out) and scroll reveals carry on below.
  var settleArrival = function () {
    targets.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("is-in");
    });
    requestAnimationFrame(function () { root.classList.remove("arriving"); });
  };
  // Listen for every arrival, not just the first: back/forward can restore
  // this page from the browser's cache and run the transition again
  window.addEventListener("arrived", settleArrival);
  if (root.classList.contains("arriving") && root.hasAttribute("data-arrived")) settleArrival();

  // A link to another page of this site (not files, new tabs or same-page anchors)
  var isPageLink = function (a) {
    if (!a || !a.href || a.target === "_blank" || a.hasAttribute("download")) return false;
    var url = new URL(a.href, location.href);
    if (url.origin !== location.origin || /^\/(assets|images)\//.test(url.pathname)) return false;
    return url.pathname !== location.pathname;
  };

  // Browsers without cross-page transitions (html.vt-fallback): fade this
  // page out, then go. The next page fades in from the head script.
  document.addEventListener("click", function (e) {
    if (!root.classList.contains("vt-fallback")) return;
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest("a[href]");
    if (!isPageLink(a)) return;
    e.preventDefault();
    try { sessionStorage.setItem("vt-nav", "1"); } catch (err) {}
    root.classList.add("leaving");
    setTimeout(function () { location.href = a.href; }, 260);
  });
  // Back/forward can restore this page exactly as it was left (faded out)
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) root.classList.remove("leaving");
  });

  // Load the next page in the background when its link is pointed at, so the
  // click is quick. Chrome does this via the speculation rules in the head;
  // this covers Safari and Firefox.
  var speculates = HTMLScriptElement.supports && HTMLScriptElement.supports("speculationrules");
  if (!speculates) {
    var warmed = {};
    var probe = document.createElement("link");
    var canPrefetch = probe.relList && probe.relList.supports && probe.relList.supports("prefetch");
    var warm = function (e) {
      var a = e.target.closest && e.target.closest("a[href]");
      if (!isPageLink(a)) return;
      var url = a.href.split("#")[0];
      if (warmed[url]) return;
      warmed[url] = true;
      if (canPrefetch) {
        var link = document.createElement("link");
        link.rel = "prefetch";
        link.href = url;
        document.head.appendChild(link);
      } else {
        fetch(url, { credentials: "same-origin" }).catch(function () {});
      }
    };
    document.addEventListener("pointerover", warm, { passive: true });
    document.addEventListener("focusin", warm);
    document.addEventListener("touchstart", warm, { passive: true });
  }

  // Custom cursor and headline spotlight (mouse/trackpad only) ------------------
  if (finePointer && !reduced) {
    root.classList.add("has-cursor");

    var cursor = document.createElement("div");
    cursor.className = "cursor";
    cursor.setAttribute("aria-hidden", "true");
    cursor.innerHTML = '<div class="cursor__box"></div>';
    document.body.appendChild(cursor);

    var px = -100, py = -100; // pointer
    var cx = -100, cy = -100; // cursor, eased toward the pointer
    var moving = false;

    var follow = function () {
      cx += (px - cx) * 0.22;
      cy += (py - cy) * 0.22;
      cursor.style.transform = "translate3d(" + cx.toFixed(1) + "px," + cy.toFixed(1) + "px,0)";
      if (Math.abs(px - cx) > 0.1 || Math.abs(py - cy) > 0.1) {
        requestAnimationFrame(follow);
      } else {
        moving = false;
      }
    };

    window.addEventListener("pointermove", function (e) {
      if (e.pointerType && e.pointerType !== "mouse") return;
      if (!cursor.classList.contains("is-visible")) {
        cx = px = e.clientX; // appear in place rather than flying in
        cy = py = e.clientY;
        cursor.classList.add("is-visible");
      }
      px = e.clientX;
      py = e.clientY;
      if (!moving) {
        moving = true;
        requestAnimationFrame(follow);
      }
    }, { passive: true });

    document.addEventListener("pointerover", function (e) {
      var t = e.target;
      cursor.classList.toggle("is-link", !!(t.closest && t.closest("a, button, [role='button']")));
    });
    document.documentElement.addEventListener("mouseleave", function () {
      cursor.classList.remove("is-visible");
    });
    window.addEventListener("pointerdown", function () { cursor.classList.add("is-down"); });
    window.addEventListener("pointerup", function () { cursor.classList.remove("is-down"); });

    // Home headline: the grey words light up around the pointer. Only runs
    // while the pointer is over the hero; word positions are measured once
    // on entry instead of every frame.
    var hero = document.querySelector(".hero");
    var words = hero ? hero.querySelectorAll(".spotlight .dim") : [];
    if (words.length) {
      var boxes = [];
      var hx = 0;
      var hy = 0;
      var spotFrame = 0;

      var paintSpot = function () {
        spotFrame = 0;
        for (var i = 0; i < words.length; i++) {
          words[i].style.setProperty("--mx", (hx - boxes[i].left).toFixed(1) + "px");
          words[i].style.setProperty("--my", (hy - boxes[i].top).toFixed(1) + "px");
        }
      };
      var measureWords = function () {
        boxes = Array.prototype.map.call(words, function (w) { return w.getBoundingClientRect(); });
      };

      hero.addEventListener("pointerenter", measureWords);
      hero.addEventListener("pointermove", function (e) {
        if (!boxes.length) measureWords();
        hx = e.clientX;
        hy = e.clientY;
        if (!spotFrame) spotFrame = requestAnimationFrame(paintSpot);
      });
      hero.addEventListener("pointerleave", function () {
        cancelAnimationFrame(spotFrame);
        spotFrame = 0;
        words.forEach(function (w) {
          w.style.removeProperty("--mx");
          w.style.removeProperty("--my");
        });
      });
      window.addEventListener("scroll", function () { boxes = []; }, { passive: true });
    }
  }

  // Copy email -------------------------------------------------------------------
  document.querySelectorAll(".copy[data-copy]").forEach(function (button) {
    if (!navigator.clipboard || !window.isSecureContext) {
      button.hidden = true;
      return;
    }
    var label = button.querySelector(".copy__label");
    var timer;
    button.addEventListener("click", function () {
      navigator.clipboard.writeText(button.dataset.copy).then(function () {
        button.classList.add("is-done");
        label.textContent = "Copied";
        clearTimeout(timer);
        timer = setTimeout(function () {
          button.classList.remove("is-done");
          label.textContent = "Copy";
        }, 2000);
      });
    });
  });

  // Download CV: the arrow drops into the tray and a tick confirms the click.
  // The browser handles the download itself.
  document.querySelectorAll("[data-dl]").forEach(function (a) {
    var timer;
    a.addEventListener("click", function () {
      a.classList.remove("is-back");
      a.classList.add("is-done");
      clearTimeout(timer);
      timer = setTimeout(function () {
        a.classList.remove("is-done");
        a.classList.add("is-back");
      }, 2200);
    });
  });

  // Case study images open full size, growing from where they sit on the
  // page and shrinking back on close --------------------------------------------
  var lightbox, lbImg, lbThumb, lbTimer;

  // Unlock page scrolling and show the page's image again, on every way out
  var unlock = function () {
    root.classList.remove("lightbox-open");
    if (lbThumb) lbThumb.style.visibility = "";
  };

  // translate + scale that puts the lightbox image exactly over `rect`
  var flipTo = function (rect) {
    var now = lbImg.getBoundingClientRect();
    return "translate(" + (rect.left - now.left) + "px," + (rect.top - now.top) + "px) scale(" + rect.width / now.width + ")";
  };

  function closeLightbox() {
    if (!lightbox.open || lightbox.classList.contains("is-closing")) return;
    var done = function () {
      lightbox.classList.remove("is-closing");
      lightbox.close();
      unlock();
    };
    if (!lightbox.classList.contains("is-flip")) return done();
    lightbox.classList.add("is-closing");
    lightbox.classList.remove("is-on");
    lbImg.style.transition = "transform 480ms var(--ease-draw)";
    lbImg.style.transform = flipTo(lbThumb.getBoundingClientRect());
    clearTimeout(lbTimer);
    lbTimer = setTimeout(done, 480);
  }

  function openLightbox(link) {
    if (!lightbox) {
      lightbox = document.createElement("dialog");
      lightbox.className = "lightbox";
      lightbox.setAttribute("aria-label", "Image viewer");
      lightbox.innerHTML =
        '<button class="lightbox__close" type="button">Close' +
        '<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
        '<path d="M6 6l12 12M18 6L6 18"/></svg></button><img alt="">';
      document.body.appendChild(lightbox);
      lbImg = lightbox.querySelector("img");

      lightbox.querySelector(".lightbox__close").addEventListener("click", closeLightbox);
      lbImg.addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", function (e) {
        if (e.target === lightbox) closeLightbox();
      });
      lightbox.addEventListener("cancel", function (e) { // Escape
        e.preventDefault();
        closeLightbox();
      });
      // closed some other way: still unlock
      lightbox.addEventListener("close", function () {
        if (!lightbox.open) unlock();
      });
    }
    var thumb = link.querySelector("img");
    var grow = !!thumb && !reduced;
    lbThumb = thumb;
    lightbox.classList.remove("is-on", "is-closing");
    lightbox.classList.toggle("is-flip", grow);
    lbImg.style.transition = "none";
    lbImg.style.transform = "";
    lbImg.alt = thumb ? thumb.alt : "";
    if (thumb) lbImg.style.setProperty("--w", thumb.getAttribute("width") + "px");
    // start from the copy already on screen; the full-size file swaps in
    lbImg.src = grow && thumb.currentSrc ? thumb.currentSrc : link.href;
    root.classList.add("lightbox-open");
    lightbox.showModal();
    lightbox.scrollTop = 0;
    if (!grow) return;

    lbImg.style.transformOrigin = "0 0";
    lbImg.style.transform = flipTo(thumb.getBoundingClientRect());
    thumb.style.visibility = "hidden";
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        lbImg.style.transition = "transform 560ms var(--ease-out)";
        lbImg.style.transform = "";
        lightbox.classList.add("is-on");
      });
    });
    if (lbImg.src !== link.href) {
      var full = new Image();
      full.onload = function () {
        if (lightbox.open && lbThumb === thumb) lbImg.src = link.href;
      };
      full.src = link.href;
    }
  }

  if (window.HTMLDialogElement) {
    document.addEventListener("click", function (e) {
      var link = e.target.closest && e.target.closest("a.zoom");
      if (!link || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      openLightbox(link);
    });
  }

  // Footer year -----------------------------------------------------------------
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
