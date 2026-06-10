/* Raising Taxes — folio behaviours: theme toggle & footnote popups */
(function () {
  'use strict';

  /* ---------------- theme toggle ---------------- */
  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('rt-theme', next); } catch (e) { /* private mode */ }
    });
  }

  /* ---------------- footnote popups ---------------- */
  var openPop = null;
  var openRef = null;
  var backdrop = null;

  function closePop() {
    if (openPop) { openPop.remove(); openPop = null; }
    if (backdrop) { backdrop.remove(); backdrop = null; }
    if (openRef) { openRef.setAttribute('aria-expanded', 'false'); openRef = null; }
  }

  function isSheet() { return window.matchMedia('(max-width: 600px)').matches; }

  function showPop(ref) {
    var id = ref.getAttribute('href').slice(1);
    var note = document.getElementById(id);
    if (!note) return false;

    closePop();

    var pop = document.createElement('aside');
    pop.className = 'fn-pop';
    pop.setAttribute('role', 'note');
    pop.setAttribute('aria-label', 'Footnote ' + ref.textContent);

    var num = document.createElement('span');
    num.className = 'fn-pop-num';
    num.textContent = ref.textContent + '.';
    pop.appendChild(num);

    // clone the note's content, minus the backlink
    var clone = note.cloneNode(true);
    clone.querySelectorAll('.fn-back').forEach(function (b) { b.remove(); });
    while (clone.firstChild) pop.appendChild(clone.firstChild);

    if (isSheet()) {
      backdrop = document.createElement('div');
      backdrop.className = 'fn-backdrop';
      document.body.appendChild(backdrop);
      pop.classList.add('sheet');
      document.body.appendChild(pop);
    } else {
      document.body.appendChild(pop);
      var rect = ref.getBoundingClientRect();
      var scrollX = window.scrollX, scrollY = window.scrollY;
      var w = pop.offsetWidth, h = pop.offsetHeight;
      var left = rect.left + scrollX + rect.width / 2 - w / 2;
      left = Math.max(scrollX + 16, Math.min(left, scrollX + document.documentElement.clientWidth - w - 16));
      var top = rect.top + scrollY - h - 12;            // prefer above
      if (rect.top - h - 12 < 8) top = rect.bottom + scrollY + 12;  // else below
      pop.style.left = left + 'px';
      pop.style.top = top + 'px';
    }

    openPop = pop;
    openRef = ref;
    ref.setAttribute('aria-expanded', 'true');
    return true;
  }

  document.querySelectorAll('a.fn-ref').forEach(function (ref) {
    ref.setAttribute('aria-expanded', 'false');
    ref.addEventListener('click', function (ev) {
      ev.preventDefault();
      if (openRef === ref) { closePop(); return; }
      showPop(ref);
    });
  });

  document.addEventListener('click', function (ev) {
    if (!openPop) return;
    if (openPop.contains(ev.target)) return;
    if (openRef && (ev.target === openRef || openRef.contains(ev.target))) return;
    closePop();
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && openPop) {
      var ref = openRef;
      closePop();
      if (ref) ref.focus();
    }
  });

  window.addEventListener('resize', closePop);

  /* ---------------- arrow-key chapter navigation ---------------- */
  document.addEventListener('keydown', function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    if (openPop) return;
    var dest = null;
    if (ev.key === 'ArrowLeft') dest = document.body.dataset.prev;
    if (ev.key === 'ArrowRight') dest = document.body.dataset.next;
    if (dest) location.href = dest;
  });
})();
