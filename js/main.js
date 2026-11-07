/* Acseda landing page: progressive enhancements, no runtime dependencies. */
(() => {
  'use strict';
  const root = document.documentElement;
  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 980px)');
  const compactPackages = matchMedia('(max-width: 600px)');
  root.classList.add('js');

  // User-visible strings, chosen by the page language (<html lang>). Each language has its own page; nothing redirects.
  const strings = {
    en: {
      locale: 'en-US',
      currency: '$',
      menuOpen: 'Open menu',
      menuClose: 'Close menu',
      required: {
        name: 'Please enter your name.',
        company: 'Please enter your company.',
        email: 'Please enter your email address.',
        phone: 'Please enter your phone number.',
        users: 'Please enter your number of users.',
      },
      invalidEmail: 'Enter a valid email address, such as name@company.com.',
      invalidPhone: 'Enter a valid phone number, including your country code.',
      invalidUsers: 'Enter a whole number of users between 1 and 100,000.',
      chooseIndustry: 'Please choose your industry.',
      formInvalid: 'Please correct the highlighted fields.',
      formPreview: 'Thank you. Your Secure Check form is complete. This is a preview: no booking has been sent. To schedule, contact hello@acsedasec.com or +297 000 0000.',
    },
    nl: {
      locale: 'nl-NL',
      // Dutch convention: currency sign, non-breaking space, amount ($ 1.109).
      currency: '$\u00a0',
      menuOpen: 'Menu openen',
      menuClose: 'Menu sluiten',
      required: {
        name: 'Vul uw naam in.',
        company: 'Vul uw bedrijfsnaam in.',
        email: 'Vul uw e-mailadres in.',
        phone: 'Vul uw telefoonnummer in.',
        users: 'Vul het aantal gebruikers in.',
      },
      invalidEmail: 'Vul een geldig e-mailadres in, bijvoorbeeld naam@bedrijf.com.',
      invalidPhone: 'Vul een geldig telefoonnummer in, inclusief landnummer.',
      invalidUsers: 'Vul een heel getal tussen 1 en 100.000 in.',
      chooseIndustry: 'Kies uw branche.',
      formInvalid: 'Controleer de gemarkeerde velden.',
      formPreview: 'Dank u wel. Uw aanvraag voor een Secure Check is volledig ingevuld. Dit is een voorbeeldversie: er is geen afspraak verstuurd. Neem voor een afspraak contact op via hello@acsedasec.com of +297 000 0000.',
    },
  };
  const t = strings[(root.lang || 'en').slice(0, 2).toLowerCase()] || strings.en;

  // The menu button and its links form a single keyboard focus loop.
  const toggle = $('.menu-toggle');
  const navigation = $('#navigation');
  const header = $('.site-header');
  let menuOpen = false;
  const setMenu = (open, restoreFocus = false) => {
    menuOpen = open && mobile.matches;
    toggle.setAttribute('aria-expanded', String(menuOpen));
    toggle.setAttribute('aria-label', menuOpen ? t.menuClose : t.menuOpen);
    navigation.classList.toggle('is-open', menuOpen);
    document.body.classList.toggle('menu-open', menuOpen);
    // Inert prevents keyboard and assistive technology access to the covered page.
    $('main').inert = menuOpen;
    $('footer').inert = menuOpen;
    $('.logo', header).inert = menuOpen;
    navigation.inert = mobile.matches && !menuOpen;
    if (restoreFocus) toggle.focus();
  };
  toggle.addEventListener('click', () => setMenu(!menuOpen));
  $$('a', navigation).forEach(link => link.addEventListener('click', () => setMenu(false, true)));
  document.addEventListener('keydown', event => {
    if (!menuOpen) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      setMenu(false, true);
    }
    if (event.key === 'Tab') {
      const focusable = [toggle, ...$$('a[href], button', navigation)];
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    }
  });
  mobile.addEventListener('change', () => setMenu(false));
  setMenu(false);

  // Scroll work is batched into one animation frame.
  const navLinks = $$('.nav-links a');
  const navTargets = navLinks.map(link => $(link.getAttribute('href')));
  const steps = $('.steps-wrap');
  let scrollQueued = false;
  function updateScroll() {
    scrollQueued = false;
    header.classList.toggle('scrolled', window.scrollY > 12);
    let active = null;
    navTargets.forEach((section, index) => {
      const box = section.getBoundingClientRect();
      if (box.top <= 160 && box.bottom > 160) active = index;
    });
    navLinks.forEach((link, index) => {
      link.classList.toggle('active', index === active);
      if (index === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    const box = steps.getBoundingClientRect();
    const progress = Math.max(0, Math.min(1, (innerHeight * .8 - box.top) / (box.height + innerHeight * .25)));
    steps.style.setProperty('--progress', reduced.matches ? 1 : progress);
  }
  const queueScroll = () => {
    if (!scrollQueued) { scrollQueued = true; requestAnimationFrame(updateScroll); }
  };
  addEventListener('scroll', queueScroll, { passive: true });
  addEventListener('resize', queueScroll, { passive: true });
  updateScroll();

  // Every reveal is observed before the class that hides it is enabled.
  const counters = $$('[data-count]');
  const completedCounters = new WeakSet();
  const countFrames = new Map();
  const formatter = new Intl.NumberFormat(t.locale);
  function countUp(element) {
    if (completedCounters.has(element)) return;
    completedCounters.add(element);
    const target = Number(element.dataset.count);
    if (reduced.matches) return;
    const started = performance.now();
    function frame(now) {
      const fraction = Math.min(1, (now - started) / 1100);
      element.textContent = formatter.format(Math.round(target * (1 - (1 - fraction) ** 3)));
      if (fraction < 1 && !reduced.matches) countFrames.set(element, requestAnimationFrame(frame));
      else { element.textContent = formatter.format(target); countFrames.delete(element); }
    }
    countFrames.set(element, requestAnimationFrame(frame));
  }
  $$('.stagger').forEach(group => [...group.children].forEach((child, index) => {
    child.style.setProperty('--reveal-delay', `${Math.min(index % 4, 3) * 90}ms`);
  }));
  $$('.entrance').forEach((element, index) => element.style.setProperty('--entrance-delay', `${index * 100}ms`));
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      });
    }, { threshold: .08, rootMargin: '0px 0px -20px 0px' });
    $$('.reveal').forEach(element => revealObserver.observe(element));
    const countObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) { countUp(entry.target); countObserver.unobserve(entry.target); }
      });
    }, { threshold: .5 });
    counters.forEach(element => countObserver.observe(element));
    if (!reduced.matches) root.classList.add('motion');
  }

  // Timeline loops as one sequence, pausing when outside the viewport.
  const timeline = $('.timeline');
  const events = $$('.event', timeline);
  let timelineTimer;
  let timelineVisible = true;
  function stopTimeline() {
    clearTimeout(timelineTimer);
    events.forEach(event => event.classList.remove('event-shown', 'event-pending'));
  }
  function startTimeline() {
    stopTimeline();
    if (reduced.matches || document.hidden || !timelineVisible) return;
    events.forEach(event => event.classList.add('event-pending'));
    let index = 0;
    function next() {
      if (index < events.length) {
        events[index++].classList.add('event-shown');
        timelineTimer = setTimeout(next, 1600);
      } else timelineTimer = setTimeout(startTimeline, 8000);
    }
    timelineTimer = setTimeout(next, 800);
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      timelineVisible = entries[0].isIntersecting;
      if (timelineVisible) startTimeline(); else stopTimeline();
    }).observe(timeline);
  } else startTimeline();

  // Diagram and legend share layer keys, supporting mouse and keyboard.
  const layerTargets = $$('[data-layer]');
  function highlightLayer(key) {
    layerTargets.forEach(element => element.classList.toggle('layer-highlight', element.dataset.layer === key));
  }
  layerTargets.forEach(element => {
    element.addEventListener('mouseenter', () => highlightLayer(element.dataset.layer));
    element.addEventListener('mouseleave', () => highlightLayer(document.activeElement?.dataset.layer));
    element.addEventListener('focus', () => highlightLayer(element.dataset.layer));
    element.addEventListener('blur', () => highlightLayer(null));
  });

  const tabs = $$('.package-tabs button');
  const packageCards = $$('[data-package-card]');
  let selectedPackage = 'essentials';
  function selectPackage(value) {
    selectedPackage = value;
    tabs.forEach(tab => tab.setAttribute('aria-pressed', String(tab.dataset.package === value)));
    packageCards.forEach(card => {
      const inactive = compactPackages.matches && card.dataset.packageCard !== value;
      card.classList.toggle('mobile-inactive', inactive);
      card.inert = inactive;
    });
  }
  tabs.forEach(tab => tab.addEventListener('click', () => selectPackage(tab.dataset.package)));
  compactPackages.addEventListener('change', () => selectPackage(selectedPackage));
  selectPackage(selectedPackage);

  const calcPackage = $('#calc-package');
  const calcUsers = $('#calc-users');
  const calcServers = $('#calc-servers');
  const calcTotal = $('#calc-total');
  function updatePrice() {
    const one = calcPackage.value === 'one';
    $('#calc-servers-label').hidden = !one;
    calcServers.disabled = !one;
    // Preserve invalid input for correction, but never display NaN or a misleading total.
    const valid = calcUsers.validity.valid && calcUsers.value !== '' && (!one || (calcServers.validity.valid && calcServers.value !== ''));
    [calcUsers, calcServers].forEach(input => input.setAttribute('aria-invalid', String(!input.disabled && (!input.validity.valid || input.value === ''))));
    const calcScan = $('#calc-scan');
    $('#calc-scan-label').hidden = one;
    // Quarterly external scanning is included in One; Essentials can add it for $79/month.
    const total = one ? 349 + Number(calcUsers.value) * 32 + Number(calcServers.value) * 60 : 99 + Number(calcUsers.value) * 15 + (calcScan.checked ? 79 : 0);
    calcTotal.textContent = valid ? `${t.currency}${formatter.format(total)}` : '—';
  }
  [calcPackage, calcUsers, calcServers, $('#calc-scan')].forEach(input => input.addEventListener('input', updatePrice));
  $('.calculator').hidden = false;
  updatePrice();

  // Front-end preview only: no data is sent or retained.
  const form = $('#secure-check');
  const submitButton = $('button[type=submit]', form);
  submitButton.disabled = false;
  const fields = $$('input, select', form);
  function validate(field) {
    let message = '';
    if (field.name === 'industry' && !field.value) message = t.chooseIndustry;
    else if (!field.value.trim()) message = t.required[field.name];
    else if (field.type === 'email' && field.validity.typeMismatch) message = t.invalidEmail;
    else if (field.name === 'phone' && (!/^[+()\d\s.\-]{6,30}$/.test(field.value.trim()) || field.value.replace(/\D/g, '').length < 6)) message = t.invalidPhone;
    else if (field.name === 'users' && !field.validity.valid) message = t.invalidUsers;
    field.setAttribute('aria-invalid', String(Boolean(message)));
    $(`#error-${field.name}`).textContent = message;
    return !message;
  }
  fields.forEach(field => {
    field.addEventListener('blur', () => { if (field.value || field.hasAttribute('aria-invalid')) validate(field); });
    field.addEventListener('input', () => { if (field.getAttribute('aria-invalid') === 'true') validate(field); });
  });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const invalid = fields.filter(field => !validate(field));
    if (invalid.length) {
      $('#form-status').textContent = t.formInvalid;
      invalid[0].focus();
      return;
    }
    // TODO: Connect an approved booking endpoint here; await its response before showing a confirmed booking.
    form.classList.add('submitted');
    $('#form-status').textContent = t.formPreview;
    $('#form-status').focus();
    form.reset();
  });
  $('.contact-actions .button').addEventListener('click', event => {
    event.preventDefault();
    form.scrollIntoView({ behavior: reduced.matches ? 'instant' : 'smooth', block: 'start' });
    $('#contact-name').focus({ preventScroll: true });
  });

  let blinkTimer;
  function scheduleBlink() {
    clearTimeout(blinkTimer);
    if (reduced.matches || document.hidden || !finePointer.matches) return;
    blinkTimer = setTimeout(() => {
      $$('.owl').forEach(owl => {
        owl.classList.add('blink');
        setTimeout(() => owl.classList.remove('blink'), 240);
      });
      scheduleBlink();
    }, 6000 + Math.random() * 4000);
  }
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  const cursorOwls = $$('.cursor-owl');
  let pointerFrame = false;
  addEventListener('pointermove', event => {
    if (reduced.matches || !finePointer.matches || event.pointerType === 'touch' || pointerFrame) return;
    pointerFrame = true;
    requestAnimationFrame(() => {
      pointerFrame = false;
      cursorOwls.forEach(owl => {
        const box = owl.getBoundingClientRect();
        if (box.bottom < 0 || box.top > innerHeight) return;
        const x = Math.max(-1.1, Math.min(1.1, (event.clientX - box.left - box.width / 2) / 250));
        const y = Math.max(-.8, Math.min(.8, (event.clientY - box.top - box.height / 2) / 250));
        owl.style.setProperty('--pupil-x', `${x}px`);
        owl.style.setProperty('--pupil-y', `${y}px`);
      });
    });
  }, { passive: true });
  function syncMotion() {
    if (reduced.matches) {
      root.classList.remove('motion');
      countFrames.forEach((id, element) => {
        cancelAnimationFrame(id); element.textContent = formatter.format(Number(element.dataset.count));
      });
      countFrames.clear();
      cursorOwls.forEach(owl => { owl.style.removeProperty('--pupil-x'); owl.style.removeProperty('--pupil-y'); });
    } else if ('IntersectionObserver' in window) root.classList.add('motion');
    startTimeline(); scheduleBlink(); updateScroll();
  }
  reduced.addEventListener('change', syncMotion);
  document.addEventListener('visibilitychange', () => { startTimeline(); scheduleBlink(); });
  scheduleBlink();
})();
