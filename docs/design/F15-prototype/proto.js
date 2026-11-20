/*
 * F15 prototype renderer (not app code). Draws the Today screen and the Planner week view with
 * fixed sample data, using only CSS tokens, so each direction is its stylesheet alone.
 * Query: ?screen=today|planner &theme=light|dark &lang=en|uz|ru &chrome=0 (hides the switcher).
 * Icons are simplified line icons in the style of Lucide (ISC licence), drawn inline.
 */
(function () {
  const q = new URLSearchParams(location.search);
  const screen = q.get('screen') === 'planner' ? 'planner' : 'today';
  const theme = q.get('theme') === 'dark' ? 'dark' : 'light';
  const lang = ['en', 'uz', 'ru'].includes(q.get('lang')) ? q.get('lang') : 'en';
  document.documentElement.dataset.theme = theme;
  document.documentElement.lang = lang;

  // Copy from the app's dictionaries (src/i18n/{en,uz,ru}.ts) where it exists.
  const T = {
    en: {
      brand: 'Discipline', tagline: 'Tracker', dashboard: 'Dashboard', planner: 'Daily Planner', analytics: 'Analytics',
      schedule: 'Smart Schedule', vocabulary: 'Vocabulary', sHome: 'Home', sPlanner: 'Planner', sStats: 'Stats', sSchedule: 'Schedule',
      sWords: 'Words', signOut: 'Sign out', today: 'Today', date: 'Wednesday, 25 November', now: 'Now', next: 'Next',
      done: 'Done', partly: 'Partly', skip: 'Skip', focusing: 'Focusing', on: 'On: Essay draft', distracted: 'I got distracted',
      oneDistraction: '1 distraction', finish: 'Finish', stop: 'Stop early', timeline: "Today's blocks", sleep: 'Slept 7 h 20 min',
      energy: 'Energy 4 of 5', planned: 'Planned', sDone: 'Done', sPartial: 'Partly done', sSkipped: 'Skipped', sProgress: 'In progress',
      restNote: 'Rest counts too.', day: 'Day', week: 'Week', range: 'Mon, Nov 23 – Sun, Nov 29', addBlock: 'Add a block',
      addRepeating: 'Add a repeating block', categories: 'Categories', hint: 'Drag a block to move it, or its lower edge to change its length.',
      conflict: "Gym didn't fit — something else is planned then.", placeAnyway: 'Place anyway', skipWeek: 'Skip this week',
      notThisWeek: 'Gym: not this week', days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], language: 'English', themeName: 'Theme',
      b: { run: 'Morning run', lectures: 'Lectures', inbox: 'Inbox & errands', lunch: 'Lunch & a walk', reading: 'Reading',
        essay: 'Essay draft', gym: 'Gym', focus: 'Focus', seminar: 'Seminar', walk: 'Long walk', call: 'Call home' },
      cat: { focus: 'Deep Work', study: 'Study', admin: 'Admin', exercise: 'Gym', rest: 'Rest', personal: 'Personal' },
    },
    uz: {
      brand: 'Discipline', tagline: 'Tracker', dashboard: 'Bosh sahifa', planner: 'Kunlik reja', analytics: 'Tahlil',
      schedule: 'Aqlli jadval', vocabulary: 'Lugʻat', sHome: 'Bosh', sPlanner: 'Reja', sStats: 'Tahlil', sSchedule: 'Jadval',
      sWords: 'Soʻzlar', signOut: 'Chiqish', today: 'Bugun', date: '25-noyabr, chorshanba', now: 'Hozir', next: 'Keyingi',
      done: 'Bajarildi', partly: 'Qisman', skip: 'Oʻtkazish', focusing: 'Diqqat', on: 'Blok: Insho qoralamasi', distracted: 'Chalgʻidim',
      oneDistraction: '1 marta chalgʻish', finish: 'Tugatish', stop: 'Erta toʻxtatish', timeline: 'Bugungi bloklar', sleep: '7 soat 20 daqiqa uyqu',
      energy: 'Energiya: 5 dan 4', planned: 'Rejada', sDone: 'Bajarildi', sPartial: 'Qisman bajarildi', sSkipped: 'Oʻtkazildi', sProgress: 'Jarayonda',
      restNote: 'Dam olish ham hisoblanadi.', day: 'Kun', week: 'Hafta', range: '23-noyabr – 29-noyabr', addBlock: 'Blok qoʻshish',
      addRepeating: 'Takrorlanuvchi blok qoʻshish', categories: 'Toifalar', hint: 'Blokni surib koʻchiring yoki pastki chetidan tortib uzunligini oʻzgartiring.',
      conflict: 'Sport sigʻmadi — bu vaqtda boshqa narsa rejalashtirilgan.', placeAnyway: 'Baribir qoʻyish', skipWeek: 'Bu hafta oʻtkazib yuborish',
      notThisWeek: 'Sport: bu hafta emas', days: ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya'], language: 'Oʻzbekcha', themeName: 'Mavzu',
      b: { run: 'Ertalabki yugurish', lectures: 'Maʼruzalar', inbox: 'Xatlar va mayda ishlar', lunch: 'Tushlik va sayr', reading: 'Kitob oʻqish',
        essay: 'Insho qoralamasi', gym: 'Sport', focus: 'Diqqat', seminar: 'Seminar', walk: 'Uzoq sayr', call: 'Uyga qoʻngʻiroq' },
      cat: { focus: 'Chuqur ish', study: 'Oʻqish', admin: 'Mayda ishlar', exercise: 'Sport', rest: 'Dam olish', personal: 'Shaxsiy' },
    },
    ru: {
      brand: 'Discipline', tagline: 'Tracker', dashboard: 'Главная', planner: 'План на день', analytics: 'Аналитика',
      schedule: 'Умное расписание', vocabulary: 'Словарь', sHome: 'Главная', sPlanner: 'План', sStats: 'Аналитика', sSchedule: 'Расписание',
      sWords: 'Слова', signOut: 'Выйти', today: 'Сегодня', date: 'Среда, 25 ноября', now: 'Сейчас', next: 'Далее',
      done: 'Готово', partly: 'Частично', skip: 'Пропустить', focusing: 'Фокус', on: 'Блок: Черновик эссе', distracted: 'Отвлёкся(-лась)',
      oneDistraction: '1 отвлечение', finish: 'Завершить', stop: 'Остановить раньше', timeline: 'Блоки на сегодня', sleep: 'Сон 7 ч 20 мин',
      energy: 'Энергия 4 из 5', planned: 'В плане', sDone: 'Готово', sPartial: 'Частично', sSkipped: 'Пропущено', sProgress: 'Идёт',
      restNote: 'Отдых тоже важен.', day: 'День', week: 'Неделя', range: '23 ноября – 29 ноября', addBlock: 'Добавить блок',
      addRepeating: 'Добавить повторяющийся блок', categories: 'Категории', hint: 'Перетащите блок, чтобы перенести его, или его нижний край, чтобы изменить длину.',
      conflict: 'Спорт не поместился — на это время уже что-то запланировано.', placeAnyway: 'Всё равно поставить', skipWeek: 'Пропустить на этой неделе',
      notThisWeek: 'Спорт: не на этой неделе', days: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'], language: 'Русский', themeName: 'Тема',
      b: { run: 'Утренняя пробежка', lectures: 'Лекции', inbox: 'Почта и мелкие дела', lunch: 'Обед и прогулка', reading: 'Чтение',
        essay: 'Черновик эссе', gym: 'Спорт', focus: 'Фокус', seminar: 'Семинар', walk: 'Долгая прогулка', call: 'Звонок домой' },
      cat: { focus: 'Глубокая работа', study: 'Учёба', admin: 'Рутина', exercise: 'Спорт', rest: 'Отдых', personal: 'Личное' },
    },
  }[lang];

  const P = 'fill="none" stroke="currentColor" stroke-width="var(--icon-stroke)" stroke-linecap="var(--icon-cap)" stroke-linejoin="var(--icon-join)"';
  const svg = (d, cls = 'ic') => `<svg class="${cls}" viewBox="0 0 24 24" ${P} aria-hidden="true">${d}</svg>`;
  const I = {
    home: svg('<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'),
    calendar: svg('<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9.5h18M8 3v3M16 3v3"/>'),
    chart: svg('<path d="M4 20V10M10 20V4M16 20v-7M21 20H3"/>'),
    sparkles: svg('<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>'),
    book: svg('<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v16H5.5A1.5 1.5 0 0 0 4 20.5z"/><path d="M4 20.5A1.5 1.5 0 0 0 5.5 22H20v-3"/>'),
    settings: svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
    left: svg('<path d="M15 18l-6-6 6-6"/>'), right: svg('<path d="M9 18l6-6-6-6"/>'),
    plus: svg('<path d="M12 5v14M5 12h14"/>'), repeat: svg('<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>', 'ic ic-sm'),
    tag: svg('<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>'),
    timer: svg('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/>'),
    moon: svg('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>'), globe: svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>'),
    user: svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>'),
    sleep: svg('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>', 'ic ic-sm'), bolt: svg('<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>', 'ic ic-sm'),
  };
  const CAT_ICON = {
    focus: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    study: '<path d="M2 6h7a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H2zM22 6h-7a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h8z"/>',
    admin: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>',
    exercise: '<path d="M6.5 6.5v11M17.5 6.5v11M3 9.5v5M21 9.5v5M6.5 12h11"/>',
    rest: '<path d="M17 8h1a4 4 0 0 1 0 8h-1M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4zM6 2v2M10 2v2M14 2v2"/>',
    personal: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  };
  const catIcon = k => svg(CAT_ICON[k], 'ic ic-sm cat-ic');
  const STATUS_ICON = {
    done: '<svg class="st-ic" viewBox="0 0 20 20" aria-hidden="true"><circle class="st-fill" cx="10" cy="10" r="8"/><path class="st-mark" d="M6.5 10.2 8.8 12.5 13.5 7.8"/></svg>',
    partial: '<svg class="st-ic" viewBox="0 0 20 20" aria-hidden="true"><circle class="st-ring" cx="10" cy="10" r="7.5"/><path class="st-half" d="M10 2.5a7.5 7.5 0 0 1 0 15z"/></svg>',
    skipped: '<svg class="st-ic" viewBox="0 0 20 20" aria-hidden="true"><circle class="st-dash" cx="10" cy="10" r="7.5"/></svg>',
    in_progress: '<svg class="st-ic st-live" viewBox="0 0 20 20" aria-hidden="true"><circle class="st-ring" cx="10" cy="10" r="7.5"/><circle class="st-dot" cx="10" cy="10" r="3.5"/></svg>',
    planned: '<svg class="st-ic" viewBox="0 0 20 20" aria-hidden="true"><circle class="st-ring" cx="10" cy="10" r="7.5"/></svg>',
  };
  const STATUS_LABEL = { done: T.sDone, partial: T.sPartial, skipped: T.sSkipped, in_progress: T.sProgress, planned: T.planned };
  const chip = s => `<span class="chip chip-${s}">${STATUS_ICON[s]}<span>${STATUS_LABEL[s]}</span></span>`;

  // ---- shell -------------------------------------------------------------------------------
  const navItems = [['home', T.dashboard, T.sHome, screen === 'today'], ['calendar', T.planner, T.sPlanner, screen === 'planner'],
    ['chart', T.analytics, T.sStats], ['sparkles', T.schedule, T.sSchedule], ['book', T.vocabulary, T.sWords]];
  const sidebar = `<aside class="sidebar"><div class="brand"><span class="brand-mark"></span><div><div class="brand-name">${T.brand}</div><div class="brand-tag">${T.tagline}</div></div></div>
    <nav class="side-nav">${navItems.map(([ic, label, , on]) => `<a class="side-link${on ? ' is-on' : ''}" href="#">${I[ic]}<span>${label}</span></a>`).join('')}</nav>
    <div class="side-user"><span class="avatar">${I.user}</span><div><div class="user-name">Zarina</div><div class="user-mail">zarina@example.com</div></div></div></aside>`;
  const topbar = `<header class="topbar"><div class="topbar-brand"><span class="brand-mark"></span><span class="brand-name">${T.brand}</span></div>
    <div class="topbar-tools"><span class="tool">${I.globe}<span>${T.language}</span></span><span class="tool">${I.moon}<span>${T.themeName}</span></span></div>
    <button class="icon-btn phone-only" aria-label="Settings">${I.settings}</button></header>`;
  const bottom = `<nav class="bottom-nav">${navItems.map(([ic, , short, on]) => `<a class="bottom-link${on ? ' is-on' : ''}" href="#">${I[ic]}<span>${short}</span></a>`).join('')}</nav>`;

  // ---- Today -------------------------------------------------------------------------------
  const timeline = [
    ['07:30–08:00', T.b.run, 'exercise', 'done'], ['09:00–12:00', T.b.lectures, 'study', 'done'],
    ['12:00–13:00', T.b.lunch, 'rest', 'done'], ['13:30–14:30', T.b.inbox, 'admin', 'partial'],
    ['14:30–15:30', T.b.reading, 'personal', 'skipped'], ['16:30–18:00', T.b.essay, 'focus', 'in_progress'],
    ['19:00–20:30', T.b.gym, 'exercise', 'planned'],
  ];
  const today = `<main class="page page-today">
    <div class="page-head"><h1>${T.today}</h1><p class="page-date">${T.date}</p></div>
    <div class="today-grid">
      <div class="today-main">
        <section class="card now-card">
          <p class="eyebrow">${T.now}</p>
          <div class="now-title"><h2>${T.b.essay}</h2>${chip('in_progress')}</div>
          <p class="now-meta"><span class="time">16:30–18:00</span><span class="cat-pill" style="--c: var(--cat-focus)">${catIcon('focus')}${T.cat.focus}</span></p>
          <div class="btn-row"><button class="btn btn-primary">${T.done}</button><button class="btn btn-secondary">${T.partly}</button><button class="btn btn-ghost">${T.skip}</button></div>
          <div class="session">
            <div class="session-head"><span class="session-label">${I.timer}${T.focusing}</span><span class="session-on">${T.on}</span></div>
            <div class="timer" role="timer">24:59</div>
            <div class="session-progress"><span style="width:38%"></span></div>
            <div class="btn-row"><button class="btn btn-secondary">${T.distracted}</button><span class="muted-note">${T.oneDistraction}</span></div>
            <div class="btn-row"><button class="btn btn-primary">${T.finish}</button><button class="btn btn-ghost">${T.stop}</button></div>
          </div>
        </section>
        <section class="card checkin-card"><span class="checkin-item">${I.sleep}${T.sleep}</span><span class="checkin-item">${I.bolt}${T.energy}</span></section>
      </div>
      <section class="card timeline-card">
        <h2 class="card-title">${T.timeline}</h2>
        <ol class="timeline">${timeline.map(([time, name, cat, st]) => `
          <li class="tl-item tl-${st}${cat === 'rest' ? ' tl-rest' : ''}" style="--c: var(--cat-${cat})">
            <span class="tl-time time">${time}</span>
            <span class="tl-body"><span class="tl-name">${catIcon(cat)}<span>${name}</span></span><span class="tl-cat">${T.cat[cat]}</span></span>
            ${chip(st)}
          </li>`).join('')}</ol>
        <p class="rest-note">${T.restNote}</p>
      </section>
    </div></main>`;

  // ---- Planner week ------------------------------------------------------------------------
  const START = 6 * 60, END = 21 * 60; // the visible part of the 00:00–24:00 grid
  const blocks = [ // [dayIndex, start, end, name, cat, status, repeat]
    [0, 540, 720, T.b.lectures, 'study', 'done', 1], [0, 1080, 1170, T.b.gym, 'exercise', 'partial', 1],
    [1, 540, 660, T.b.focus + ' 1', 'focus', 'skipped', 0], [1, 840, 960, T.b.focus + ' 2', 'focus', 'done', 0],
    [2, 540, 720, T.b.lectures, 'study', 'done', 1], [2, 780, 840, T.b.lunch, 'rest', 'done', 0], [2, 990, 1080, T.b.essay, 'focus', 'in_progress', 0],
    [2, 1080, 1140, T.b.seminar, 'study', 'planned', 0],
    [3, 540, 660, T.b.focus + ' 3', 'focus', 'planned', 0], [3, 840, 960, T.b.focus + ' 4', 'focus', 'planned', 0],
    [4, 540, 720, T.b.lectures, 'study', 'planned', 1], [4, 1110, 1170, T.b.call, 'personal', 'planned', 0],
    [5, 600, 720, T.b.walk, 'rest', 'planned', 0],
  ];
  const markers = [[2, 1080, 1170, 'conflict'], [4, 1080, 1170, 'cancelled']];
  const clock = m => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
  const col = (d, phone) => {
    const own = blocks.filter(b => b[0] === d);
    const conflict = markers.find(m => m[0] === d && m[3] === 'conflict');
    return `<div class="day-col${d === 2 ? ' is-today' : ''}" role="group">
      ${markers.filter(m => m[0] === d).map(([, s, e, kind]) => `<div class="marker marker-${kind}${kind === 'conflict' ? ' lane-2' : ''}" style="top:calc(${s - START} * var(--ppm)); min-height:calc(${e - s} * var(--ppm))">
        ${kind === 'conflict' ? `<span>${T.conflict}</span><span class="marker-actions"><button class="btn btn-xs btn-secondary">${T.placeAnyway}</button><button class="btn btn-xs btn-ghost">${T.skipWeek}</button></span>` : `<span>${T.notThisWeek}</span>`}
      </div>`).join('')}
      ${own.map(([, s, e, name, cat, st, rep]) => {
        const lane = conflict && s < conflict[2] && e > conflict[1] ? ' lane-1' : '';
        return `<div class="blk blk-${st}${cat === 'rest' ? ' blk-rest' : ''}${lane}" style="--c: var(--cat-${cat}); top:calc(${s - START} * var(--ppm)); height:calc(${e - s} * var(--ppm))">
          <span class="blk-name">${catIcon(cat)}<span>${name}</span>${rep ? I.repeat : ''}</span>
          <span class="blk-time time">${clock(s)}–${clock(e)}</span>
          ${st !== 'planned' ? `<span class="blk-st">${STATUS_ICON[st]}<span class="${phone ? '' : 'sr'}">${STATUS_LABEL[st]}</span></span>` : ''}
        </div>`;
      }).join('')}
      ${d === 2 ? `<div class="now-line" style="top:calc(${15 * 60 + 10 - START} * var(--ppm))"></div>` : ''}
    </div>`;
  };
  const hours = [];
  for (let m = START; m <= END - 60; m += 60) hours.push(`<span style="top:calc(${m - START} * var(--ppm))">${clock(m)}</span>`);
  const dateNums = [23, 24, 25, 26, 27, 28, 29];
  const dots = [3, 2, 3, 2, 2, 1, 0];
  const planner = `<main class="page page-planner">
    <div class="page-head"><h1>${T.planner}</h1><div class="seg"><button>${T.day}</button><button class="is-on">${T.week}</button></div></div>
    <div class="toolbar">
      <div class="toolbar-nav"><button class="btn btn-outline btn-icon" aria-label="Previous">${I.left}</button><button class="btn btn-outline btn-icon" aria-label="Next">${I.right}</button>
        <button class="btn btn-outline">${T.today}</button><span class="range desk-only">${T.range}</span><span class="range phone-only">${T.date}</span></div>
      <div class="toolbar-actions"><button class="btn btn-primary">${I.plus}<span>${T.addBlock}</span></button><button class="btn btn-secondary">${I.repeat}<span>${T.addRepeating}</span></button><button class="btn btn-outline">${I.tag}<span>${T.categories}</span></button></div>
    </div>
    <p class="hint">${T.hint}</p>
    <div class="pills phone-only">${T.days.map((d, i) => `<button class="pill${i === 2 ? ' is-on' : ''}${i === 2 ? ' is-today' : ''}"><span>${d}</span><b>${dateNums[i]}</b><i class="dots">${'<em></em>'.repeat(dots[i])}</i></button>`).join('')}</div>
    <section class="card grid-card">
      <div class="grid-head desk-only"><span></span>${T.days.map((d, i) => `<span class="${i === 2 ? 'is-today' : ''}">${d} ${dateNums[i]}</span>`).join('')}</div>
      <div class="grid-body" style="height:calc(${END - START} * var(--ppm))">
        <div class="gutter">${hours.join('')}</div>
        <div class="cols desk-only">${[0, 1, 2, 3, 4, 5, 6].map(d => col(d, false)).join('')}</div>
        <div class="cols phone-only">${col(2, true)}</div>
      </div>
    </section></main>`;

  document.body.innerHTML = `<div class="app">${sidebar}<div class="main-col">${topbar}${screen === 'today' ? today : planner}</div>${bottom}</div>`;

  // A small switcher for reviewing by hand; hidden in screenshots (?chrome=0), where the phone's
  // bottom bar also sits at the end of the page so a full-page capture shows it once.
  if (q.get('chrome') === '0') document.documentElement.classList.add('shot');
  else {
    const link = (k, v) => { const n = new URLSearchParams(q); n.set(k, v); return `?${n}`; };
    const el = document.createElement('div');
    el.className = 'proto-switch';
    el.innerHTML = ['today', 'planner'].map(s => `<a href="${link('screen', s)}">${s}</a>`).join('') + ' · ' +
      ['light', 'dark'].map(s => `<a href="${link('theme', s)}">${s}</a>`).join('') + ' · ' +
      ['en', 'uz', 'ru'].map(s => `<a href="${link('lang', s)}">${s}</a>`).join('') + ' · <a href="index.html">all</a>';
    document.body.appendChild(el);
  }
})();
