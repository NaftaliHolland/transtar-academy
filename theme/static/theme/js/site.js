/* Progressive enhancement only: every page works without this file. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* Mobile menu */
  const menuButton = $('#menuButton');
  const menu = $('#mainMenu');
  if (menuButton && menu) {
    menuButton.addEventListener('click', () => {
      const hidden = menu.classList.toggle('hidden');
      menuButton.setAttribute('aria-expanded', String(!hidden));
    });
  }

  /* Dropdown submenus */
  const closeSubmenus = (except) => {
    $$('[data-submenu-toggle]').forEach((btn) => {
      if (btn === except) return;
      btn.setAttribute('aria-expanded', 'false');
      btn.closest('li')?.removeAttribute('data-open');
    });
  };
  $$('[data-submenu-toggle]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = btn.getAttribute('aria-expanded') !== 'true';
      closeSubmenus(btn);
      btn.setAttribute('aria-expanded', String(open));
      const li = btn.closest('li');
      open ? li.setAttribute('data-open', '') : li.removeAttribute('data-open');
    });
  });
  document.addEventListener('click', () => closeSubmenus());
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const openBtn = $('[data-submenu-toggle][aria-expanded="true"]');
    if (openBtn) {
      closeSubmenus();
      openBtn.focus();
    }
  });

  /* Information dialog (tiles with a description) */
  const dialog = $('#siteDialog');
  if (dialog) {
    $$('[data-dialog-title]').forEach((btn) =>
      btn.addEventListener('click', () => {
        $('#siteDialogTitle').textContent = btn.dataset.dialogTitle;
        $('#siteDialogText').textContent = btn.dataset.dialogText || '';
        const link = $('#siteDialogLink');
        if (btn.dataset.dialogHref) {
          link.href = btn.dataset.dialogHref;
          link.textContent = btn.dataset.dialogLinkText || 'Learn more';
          link.hidden = false;
        } else {
          link.hidden = true;
        }
        dialog.showModal();
      })
    );
    $$('[data-dialog-close]', dialog).forEach((b) => b.addEventListener('click', () => dialog.close()));
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) dialog.close();
    });
  }

  /* Testimonials: show the next review by rotating the list */
  $$('[data-carousel]').forEach((root) => {
    const list = $('[data-carousel-list]', root);
    const status = $('[data-carousel-status]', root);
    const visible = Number(list.dataset.visible || 3);
    const sync = () => [...list.children].forEach((c, i) => (c.hidden = i >= visible));
    $('[data-carousel-next]', root)?.addEventListener('click', () => {
      list.append(list.firstElementChild);
      sync();
      if (status) status.textContent = `Now showing: ${list.firstElementChild.dataset.name || 'next review'}`;
    });
  });

  /* Gallery lightbox */
  const box = $('#lightbox');
  const items = $$('[data-lightbox]');
  if (box && items.length) {
    let index = 0;
    const img = $('#lightboxImage', box);
    const cap = $('#lightboxCaption', box);
    const show = (i) => {
      index = (i + items.length) % items.length;
      const a = items[index];
      img.src = a.href;
      img.alt = a.dataset.alt || '';
      cap.textContent = a.dataset.caption || '';
    };
    items.forEach((a, i) =>
      a.addEventListener('click', (e) => {
        e.preventDefault();
        show(i);
        box.showModal();
      })
    );
    $('[data-lightbox-prev]', box).addEventListener('click', () => show(index - 1));
    $('[data-lightbox-next]', box).addEventListener('click', () => show(index + 1));
    $('[data-lightbox-close]', box).addEventListener('click', () => box.close());
    box.addEventListener('click', (e) => {
      if (e.target === box) box.close();
    });
    box.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') show(index - 1);
      if (e.key === 'ArrowRight') show(index + 1);
    });
  }

  /* Dismissible alert bar (remembered for the browser session) */
  const alertBar = $('#alertBar');
  if (alertBar) {
    const key = 'alert:' + alertBar.dataset.alertId;
    try {
      if (sessionStorage.getItem(key)) alertBar.hidden = true;
    } catch (_) {}
    $('[data-alert-dismiss]', alertBar)?.addEventListener('click', () => {
      alertBar.hidden = true;
      try {
        sessionStorage.setItem(key, '1');
      } catch (_) {}
    });
  }
})();
