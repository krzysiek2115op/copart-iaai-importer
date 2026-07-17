/* ============================================================
   KREDYT KOMPAS — interactions
   ============================================================ */
(function(){
  "use strict";
  const $ = (s,c=document)=>c.querySelector(s);
  const $$ = (s,c=document)=>[...c.querySelectorAll(s)];
  const fmt = n => new Intl.NumberFormat('pl-PL',{maximumFractionDigits:0}).format(Math.max(0,Math.round(n)));

  /* ---------- Sticky nav ---------- */
  const nav = $('.nav');
  const onScroll = ()=> nav && nav.classList.toggle('scrolled', window.scrollY > 24);
  onScroll();
  window.addEventListener('scroll', onScroll, {passive:true});

  /* ---------- Hero parallax (zoom + clip-path reveal on scroll) ----------
     Efekt smooth-scroll: w miarę przewijania hero kadr (clip-path) rozsuwa się
     do pełnego, a zdjęcie tła „odjeżdża" z zoomu 1.2 → 1. Wartości startowe
     ustawia CSS (.hero: --hero-clip / --hero-zoom); tu tylko je animujemy. */
  const hero = $('.hero'), heroPhoto = $('.hero-photo');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  if(hero && heroPhoto && !reduceMotion){
    const START_CLIP = 6, START_ZOOM = 1.12, SHIFT = 0.22;   // = wartości startowe w CSS
    let ticking = false;
    const apply = ()=>{
      ticking = false;
      const y = window.scrollY;
      const range = hero.offsetHeight || window.innerHeight;
      const p = Math.min(Math.max(y / range, 0), 1);   // 0→1 przez wysokość hero
      hero.style.setProperty('--hero-shift', (Math.min(y, range)*SHIFT).toFixed(1)+'px'); // pionowy parallax
      hero.style.setProperty('--hero-clip', (START_CLIP*(1-p)).toFixed(2)+'%');
      hero.style.setProperty('--hero-zoom', (START_ZOOM-(START_ZOOM-1)*p).toFixed(4));
    };
    const onParallax = ()=>{ if(!ticking){ ticking = true; requestAnimationFrame(apply); } };
    apply();
    window.addEventListener('scroll', onParallax, {passive:true});
    window.addEventListener('resize', onParallax, {passive:true});

    /* slideshow — cross-fade co 6 s; slajd 1 ładuje się od razu, reszta leniwie */
    const slides = $$('.hero-slide', heroPhoto);
    if(slides.length > 1){
      const lazy = ()=> slides.forEach(s=>{ if(s.dataset.src && !s.getAttribute('src')) s.src = s.dataset.src; });
      ('requestIdleCallback' in window) ? requestIdleCallback(lazy) : setTimeout(lazy, 1200);
      let idx = 0, timer = 0;
      const advance = ()=>{
        slides[idx].classList.remove('is-active');
        idx = (idx + 1) % slides.length;
        slides[idx].classList.add('is-active');
      };
      const start = ()=>{ if(!timer) timer = setInterval(advance, 6000); };
      const stop  = ()=>{ clearInterval(timer); timer = 0; };
      start();
      document.addEventListener('visibilitychange', ()=> document.hidden ? stop() : start());
    }
  }

  /* ---------- Karty + kontakt: poświata podążająca za kursorem (--mx/--my) ---------- */
  if(!reduceMotion){
    $$('.card, .cinfo .ci, .form-card, .legal-card, .stats').forEach(card=>{
      card.addEventListener('pointermove', e=>{
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', (e.clientX - r.left)+'px');
        card.style.setProperty('--my', (e.clientY - r.top)+'px');
      });
    });
  }

  /* ---------- ① Menu: płynący wskaźnik „magic line" (desktop) ---------- */
  const navLinks = $('.nav-links');
  if(navLinks && matchMedia('(min-width:1024px)').matches && !reduceMotion){
    const ind = document.createElement('span');
    ind.className = 'nav-ind';
    navLinks.appendChild(ind);
    navLinks.classList.add('has-ind');
    const items = $$('a:not(.nav-cta)', navLinks);
    const move = a =>{
      ind.style.left  = a.offsetLeft+'px';
      ind.style.width = a.offsetWidth+'px';
      ind.style.top   = (a.offsetTop + a.offsetHeight + 2)+'px';
      ind.style.opacity = '1';
    };
    const reset = ()=>{ const a = $('a.active', navLinks) || items[0]; if(a) move(a); };
    items.forEach(a=> a.addEventListener('mouseenter', ()=>move(a)));
    navLinks.addEventListener('mouseleave', reset);
    window.addEventListener('resize', reset, {passive:true});
    window.addEventListener('load', reset);
    requestAnimationFrame(reset);
  }

  /* ---------- ③ Parallax zdjęć w sekcjach „split" ---------- */
  const visuals = $$('.split .visual');
  if(visuals.length && !reduceMotion){
    let vTick = false;
    const updV = ()=>{
      vTick = false; const vh = window.innerHeight;
      visuals.forEach(v=>{
        const r = v.getBoundingClientRect();
        if(r.bottom < -50 || r.top > vh+50) return;           // poza widokiem — pomiń
        const c = r.top + r.height/2 - vh/2;                   // odległość środka od środka ekranu
        v.style.setProperty('--vis-shift', Math.max(-26, Math.min(26, -c*0.06)).toFixed(1)+'px');
      });
    };
    const onV = ()=>{ if(!vTick){ vTick = true; requestAnimationFrame(updV); } };
    updV();
    window.addEventListener('scroll', onV, {passive:true});
    window.addEventListener('resize', onV, {passive:true});
  }

  /* ---------- Kompas reagujący na kursor (FAQ): igła wskazuje kursor + lekki parallax ---------- */
  const liveCompass = $('.kompas-mark--live');
  if(liveCompass && !reduceMotion){
    const needle = $('.needle', liveCompass);
    const host = liveCompass.closest('.compass-section') || document;
    let cTick = false, mx = 0, my = 0;
    const applyC = ()=>{
      cTick = false;
      const r = liveCompass.getBoundingClientRect();
      const cx = r.left + r.width/2, cy = r.top + r.height/2;
      if(needle) needle.style.transform = 'rotate('+(Math.atan2(my-cy, mx-cx)*180/Math.PI + 90).toFixed(1)+'deg)';
      liveCompass.style.transform = 'translate('+Math.max(-12,Math.min(12,(mx-cx)*0.02)).toFixed(1)+'px,'+Math.max(-12,Math.min(12,(my-cy)*0.02)).toFixed(1)+'px)';
    };
    host.addEventListener('pointermove', e=>{ mx = e.clientX; my = e.clientY; if(!cTick){ cTick = true; requestAnimationFrame(applyC); } }, {passive:true});
  }

  /* ---------- Sekcja CTA: igła kompasu wskazuje kursor, a przy fokusie — aktywne pole ---------- */
  const formCompass = $('.form-section .rose-bg svg');
  if(formCompass && !reduceMotion){
    const fNeedle = formCompass.querySelectorAll('path')[1];   // 2. path = igła
    const fSection = formCompass.closest('.form-section');
    let fTick = false, fmx = 0, fmy = 0, focusEl = null;
    const point = (tx,ty)=>{
      const r = formCompass.getBoundingClientRect();
      const cx = r.left+r.width/2, cy = r.top+r.height/2;
      if(fNeedle) fNeedle.style.transform = 'rotate('+(Math.atan2(ty-cy, tx-cx)*180/Math.PI + 90).toFixed(1)+'deg)';
    };
    const applyF = ()=>{ fTick = false;
      if(focusEl){ const fr = focusEl.getBoundingClientRect(); point(fr.left+fr.width/2, fr.top+fr.height/2); }
      else point(fmx, fmy);
    };
    fSection.addEventListener('pointermove', e=>{ fmx = e.clientX; fmy = e.clientY; if(!focusEl && !fTick){ fTick = true; requestAnimationFrame(applyF); } }, {passive:true});
    fSection.addEventListener('focusin', e=>{ if(e.target.matches('input,select,textarea')){ focusEl = e.target; applyF(); } });
    fSection.addEventListener('focusout', ()=>{ focusEl = null; });
  }

  /* ---------- Sekcja „Policz zdolność": tilt 3D zdjęcia za kursorem ---------- */
  if(!reduceMotion){
    $$('.split').forEach(split=>{
      const vis = $('.visual', split);
      if(!vis) return;
      split.addEventListener('pointermove', e=>{
        const r = vis.getBoundingClientRect();
        vis.style.setProperty('--rx', (((e.clientX-r.left)/r.width - .5)*6).toFixed(2)+'deg');
        vis.style.setProperty('--ry', ((.5 - (e.clientY-r.top)/r.height)*6).toFixed(2)+'deg');
      }, {passive:true});
      split.addEventListener('pointerleave', ()=>{ vis.style.setProperty('--rx','0deg'); vis.style.setProperty('--ry','0deg'); });
    });
  }

  /* ---------- Mobile menu ---------- */
  const burger = $('.burger');
  const links = $('.nav-links');
  if(burger && links){
    burger.addEventListener('click', ()=>{
      const open = links.classList.toggle('open');
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open);
      document.body.style.overflow = open ? 'hidden' : '';
    });
    $$('a',links).forEach(a=>a.addEventListener('click',()=>{
      links.classList.remove('open');burger.classList.remove('open');document.body.style.overflow='';
    }));
    /* reset przy powrocie do desktopu (obrót ekranu / resize) — inaczej blokada scrolla zostaje */
    window.addEventListener('resize', ()=>{
      if(window.innerWidth > 1023 && links.classList.contains('open')){
        links.classList.remove('open'); burger.classList.remove('open');
        burger.setAttribute('aria-expanded','false'); document.body.style.overflow='';
      }
    }, {passive:true});
  }

  /* ---------- Scroll reveals ---------- */
  const io = new IntersectionObserver(entries=>{
    entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('visible'); io.unobserve(e.target);} });
  },{threshold:.12});
  $$('.reveal').forEach(el=>io.observe(el));

  /* ---------- Animated counters ---------- */
  const cio = new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(!e.isIntersecting) return;
      const el = e.target, target = parseFloat(el.dataset.count), dur = 1600, t0 = performance.now();
      const suffix = el.dataset.suffix || '';
      const dec = el.dataset.dec ? parseInt(el.dataset.dec) : 0;
      if(reduceMotion){
        el.textContent = (dec ? target.toFixed(dec).replace('.',',') : fmt(target)) + suffix;
        cio.unobserve(el); return;
      }
      (function tick(t){
        const p = Math.min((t-t0)/dur,1), eased = 1-Math.pow(1-p,3);
        el.textContent = (dec ? (target*eased).toFixed(dec).replace('.',',') : fmt(target*eased)) + suffix;
        if(p<1) requestAnimationFrame(tick);
      })(t0);
      cio.unobserve(el);
    });
  },{threshold:.5});
  $$('[data-count]').forEach(el=>cio.observe(el));

  /* ---------- FAQ accordion ---------- */
  $$('.faq-item').forEach(item=>{
    const q = $('.faq-q',item), a = $('.faq-a',item);
    q.addEventListener('click',e=>{
      if(!reduceMotion){
        const rect = q.getBoundingClientRect(), kb = e.detail === 0;
        q.style.setProperty('--rx', kb ? '50%' : (e.clientX - rect.left)+'px');
        q.style.setProperty('--ry', kb ? '50%' : (e.clientY - rect.top)+'px');
        q.classList.remove('rippling'); void q.offsetWidth; q.classList.add('rippling');
      }
      const open = item.classList.contains('open');
      $$('.faq-item.open').forEach(o=>{ o.classList.remove('open'); $('.faq-a',o).style.maxHeight = null; $('.faq-q',o).setAttribute('aria-expanded','false');});
      if(!open){ item.classList.add('open'); a.style.maxHeight = a.scrollHeight+'px'; q.setAttribute('aria-expanded','true'); }
    });
  });

  /* ============================================================
     CALCULATOR — szacunkowa analiza zdolności kredytowej
     Metodyka (uproszczona, zgodna z praktyką rynkową):
     - dochód uznawany: korekta wg formy zatrudnienia
     - koszty utrzymania gospodarstwa domowego (per osoba)
     - limit DSTI: 50% dochodu netto (rekomendacja KNF)
     - bufor stresowy: oprocentowanie + 2,5 p.p. przy liczeniu zdolności
     - rata annuitetowa
     ============================================================ */
  const calc = $('#calc-form');
  if(calc){
    const out = {
      capacity: $('#r-capacity'), price: $('#r-price'), payment: $('#r-payment'),
      income: $('#r-income'), costs: $('#r-costs'), dsti: $('#r-dsti'),
      dstiBar: $('#dsti-bar'), dstiBox: $('#dsti-box'), reco: $('#r-reco')
    };
    const incomeFactor = { uop_nieokreslony:1.0, uop_okreslony:0.95, b2b:0.85, zlecenie:0.80 };
    const LIVING_FIRST = 1450, LIVING_NEXT = 950, DSTI_LIMIT = 0.50, STRESS = 2.5;

    const annuityCapital = (payment, ratePct, years)=>{
      const i = (ratePct/100)/12, n = years*12;
      if(i<=0) return payment*n;
      return payment * (1 - Math.pow(1+i,-n)) / i;
    };
    const annuityPayment = (capital, ratePct, years)=>{
      const i = (ratePct/100)/12, n = years*12;
      if(i<=0) return capital/n;
      return capital * i / (1 - Math.pow(1+i,-n));
    };

    /* płynne doliczanie wyniku do nowej wartości (zamiast skoku) */
    const animVal = (el, to, suffix='', dec=0)=>{
      if(reduceMotion){ el._cur = to; el.textContent = (dec ? to.toFixed(dec).replace('.',',') : fmt(to)) + suffix; return; }
      cancelAnimationFrame(el._raf||0);
      const from = (typeof el._cur === 'number') ? el._cur : to, t0 = performance.now(), dur = 480;
      (function tk(t){
        const p = Math.min((t-t0)/dur,1), e = 1-Math.pow(1-p,3), v = from+(to-from)*e;
        el._cur = v;
        el.textContent = (dec ? v.toFixed(dec).replace('.',',') : fmt(v)) + suffix;
        if(p<1) el._raf = requestAnimationFrame(tk);
      })(t0);
    };

    const recompute = ()=>{
      const income   = parseFloat($('#f-income').value)||0;
      const co       = parseFloat($('#f-coincome').value)||0;
      const form     = $('#f-form').value;
      const oblig    = parseFloat($('#f-oblig').value)||0;
      const limits   = parseFloat($('#f-limits').value)||0;
      const people   = parseInt($('#f-people').value)||1;
      const down     = parseFloat($('#f-down').value)||0;
      const years    = parseInt($('#f-years').value)||25;
      const rate     = parseFloat($('#f-rate').value)||6.8;
      $('#f-years-out').textContent = years+' lat';
      $('#f-rate-out').textContent  = rate.toFixed(1).replace('.',',')+'%';

      const recognized = income*(incomeFactor[form]||1) + co*0.95;
      const living = LIVING_FIRST + Math.max(0,people-1)*LIVING_NEXT;
      const limitBurden = limits*0.03; // 3% przyznanych limitów (praktyka bankowa)
      const free = recognized - living - oblig - limitBurden;
      const maxPayment = Math.min(recognized*DSTI_LIMIT - oblig - limitBurden, free*0.9);

      let capacity = 0, payment = 0, dsti = 0;
      if(maxPayment>200){
        capacity = annuityCapital(maxPayment, rate+STRESS, years); // bufor stresowy
        capacity = Math.round(capacity/1000)*1000;
        payment  = annuityPayment(capacity, rate, years);          // realna rata
        dsti     = (payment+oblig+limitBurden)/recognized*100;
      }
      animVal(out.capacity, capacity, ' zł');
      animVal(out.price,    capacity+down, ' zł');
      animVal(out.payment,  payment, ' zł/mc');
      animVal(out.income,   recognized, ' zł');
      animVal(out.costs,    living+oblig+limitBurden, ' zł');
      const d = Math.min(100,Math.max(0,dsti));
      animVal(out.dsti, d, '%');
      out.dstiBar.style.width  = d+'%';
      out.dstiBox.classList.toggle('warn', d>45);

      if(capacity<=0){
        out.reco.innerHTML = 'Przy podanych parametrach zdolność jest <b>ograniczona</b>. To częsta sytuacja — zwykle da się ją poprawić (konsolidacja zobowiązań, dłuższy okres, drugi kredytobiorca). <b>Skontaktuj się z nami</b>, przeanalizujemy Twój przypadek bezpłatnie.';
      } else if(d>45){
        out.reco.innerHTML = 'Wynik na granicy bezpiecznego wskaźnika DSTI. <b>Umów bezpłatną konsultację</b> — dobierzemy bank, który najlepiej policzy Twój dochód, i zwiększymy realną zdolność.';
      } else {
        out.reco.innerHTML = 'Dobra wiadomość: Twoje parametry wyglądają obiecująco. Banki różnią się w wyliczeniach nawet o <b>15–20%</b> — <b>umów bezpłatną konsultację</b>, a wskażemy 3 najkorzystniejsze oferty dla Twojego profilu.';
      }
    };
    calc.addEventListener('input', recompute);
    recompute();
  }

  /* ---------- Suwaki: wypełnienie tracka wg wartości (--fill) ---------- */
  $$('input[type=range]').forEach(r=>{
    const fill = ()=>{
      const min = parseFloat(r.min)||0, max = parseFloat(r.max)||100;
      r.style.setProperty('--fill', ((r.value - min)/(max - min)*100).toFixed(1)+'%');
    };
    fill();
    r.addEventListener('input', fill);
  });

  /* ---------- Forms (front-end only) ---------- */
  $$('form[data-demo]').forEach(form=>{
    $$('input[required],textarea[required],select[required]',form).forEach(inp=>{
      inp.addEventListener('blur',()=>{
        inp.closest('.field')?.classList.toggle('error', !inp.checkValidity());
      });
      inp.addEventListener('input',()=>{
        if(inp.checkValidity()) inp.closest('.field')?.classList.remove('error');
      });
    });
    form.addEventListener('submit',e=>{
      e.preventDefault();
      let ok = true;
      $$('input[required],textarea[required],select[required]',form).forEach(inp=>{
        const bad = !inp.checkValidity();
        inp.closest('.field')?.classList.toggle('error',bad);
        if(bad) ok = false;
      });
      const consent = $('input[type=checkbox][required]',form);
      if(consent && !consent.checked){ ok=false; consent.focus(); }
      if(!ok) return;

      const showOk = ()=>{
        form.style.display='none';
        const okBox = form.parentElement.querySelector('.form-ok');
        if(okBox) okBox.style.display='block';
      };

      // Dopóki nie ustawisz prawdziwego endpointu Formspree (action) — działa tryb demo.
      const endpoint = form.getAttribute('action');
      if(!endpoint || endpoint.indexOf('YOUR_FORM_ID') !== -1){ showOk(); return; }

      const btn = form.querySelector('button[type=submit]');
      if(btn) btn.disabled = true;
      fetch(endpoint, { method:'POST', body:new FormData(form), headers:{ 'Accept':'application/json' } })
        .then(r=>{
          if(r.ok){ showOk(); }
          else { if(btn) btn.disabled=false; alert('Nie udało się wysłać zgłoszenia. Zadzwoń: +48 500 678 799.'); }
        })
        .catch(()=>{ if(btn) btn.disabled=false; alert('Brak połączenia. Spróbuj ponownie lub zadzwoń: +48 500 678 799.'); });
    });
  });
})();
