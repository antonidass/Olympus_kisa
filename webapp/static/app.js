// State
const state = {
  mode: 'voice',   // 'voice' | 'image'
  scenario: null,
  scenes: [],
  activeSceneBase: null,
  currentAudio: null,
  currentPlayingCard: null,
  // Hub
  summaries: [],
  hubSelectedName: null,
  hubFilter: 'all',
  hubSceneCache: {},   // key: `${mode}::${scenario}`
  hubSearchTerm: '',
  // CosyVoice progress (один раз запускаем — одна сцена в работе)
  cosy: {
    timer: null,
    base: null,
    startedAt: 0,
    lastProduced: 0,
    lastProducedAt: 0,
    logOpen: false,           // пользователь открыл <details> c логом
    autoOpenedOnFail: false,  // мы один раз принудительно раскрывали его при ошибке
    logScrollPinnedBottom: true, // если юзер не листал — продолжаем автоскролл
  },
};

// DOM
const $ = (id) => document.getElementById(id);
const scenarioTitle = $('scenario-title');
const sceneNavList = $('scene-nav-list');
const sceneDetail = $('scene-detail');
const emptyState = $('empty-state');
const toastEl = $('toast');

// ── Mode-aware URL builders ───────────────────────────────────────────────

function api() {
  if (state.mode === 'image') {
    return {
      myths: '/api/images/myths',
      scenes:  (name) => `/api/images/${encodeURIComponent(name)}/scenes`,
      select:  (name) => `/api/images/${encodeURIComponent(name)}/select`,
      regen:   (name) => `/api/images/${encodeURIComponent(name)}/regen`,
      finalize:(name) => `/api/images/${encodeURIComponent(name)}/finalize`,
    };
  }
  return {
    myths: '/api/scenarios-summary',
    scenes:  (name) => `/api/scenes/${encodeURIComponent(name)}`,
    select:  (name) => `/api/select/${encodeURIComponent(name)}`,
    regen:   (name) => `/api/regenerate-cosyvoice/${encodeURIComponent(name)}`,
    regenEL: (name) => `/api/regenerate-elevenlabs/${encodeURIComponent(name)}`,
    finalize:(name) => `/api/finalize/${encodeURIComponent(name)}`,
  };
}

function modeLabel() {
  return state.mode === 'image' ? 'Ревью изображений' : 'Ревью озвучки';
}

function cacheKey(scenario) {
  return `${state.mode}::${scenario}`;
}

// ── Init ──────────────────────────────────────────────────────────────────

async function init() {
  // Стартуем с chooser
  setView('chooser');
  setupBrandAndCrumbs();
  setupHubBindings();
  loadChooserMeta().catch(err => console.warn('chooser meta load failed', err));
}

function setView(view) {
  document.body.dataset.view = view;
  if (view === 'hub' || view === 'chooser') {
    stopAudio();
    stopCosyProgress();
  }
}

function setMode(mode) {
  state.mode = mode;
  document.body.dataset.mode = mode;
  const crumb = $('crumb-hub');
  if (crumb) crumb.textContent = modeLabel();
  // Кнопка финализации одинаковая в обоих режимах — «Собрать финал»
  const finLabel = $('finalize-label');
  if (finLabel) finLabel.textContent = 'Собрать финал';
}

function setupBrandAndCrumbs() {
  // Клик по бренду → chooser
  $('brand-link').addEventListener('click', (e) => {
    e.preventDefault();
    goToChooser();
  });

  // Клик по "Ревью озвучки/изображений" → хаб текущего режима
  $('crumb-hub').addEventListener('click', (e) => {
    e.preventDefault();
    setView('hub');
    loadHub().catch(err => console.error('hub reload failed', err));
  });
}

function goToChooser() {
  setView('chooser');
  loadChooserMeta().catch(() => {});
}

// Подтягиваем статистику для обеих плиток чузера
async function loadChooserMeta() {
  const [voiceSum, imageSum] = await Promise.allSettled([
    fetchJSON('/api/scenarios-summary'),
    fetchJSON('/api/images/myths'),
  ]);
  fillChooserMeta('chooser-voice-meta', voiceSum);
  fillChooserMeta('chooser-image-meta', imageSum);
}

function fillChooserMeta(elId, settled) {
  const el = $(elId);
  if (!el) return;
  if (settled.status !== 'fulfilled') {
    el.textContent = 'нет данных';
    el.classList.add('err');
    return;
  }
  const list = settled.value || [];
  if (!list.length) {
    el.textContent = 'нет доступных мифов';
    return;
  }
  const totalScenes = list.reduce((s, m) => s + (m.scene_count || 0), 0);
  const done = list.reduce((s, m) => s + (m.done || 0), 0);
  el.innerHTML = `<b>${list.length}</b> ${plural(list.length, 'миф', 'мифа', 'мифов')} · ` +
                 `<b>${totalScenes}</b> ${plural(totalScenes, 'сцена', 'сцены', 'сцен')} · ` +
                 `проверено <b>${done}</b>`;
}

// Обработчики плиток chooser
document.addEventListener('click', (e) => {
  const card = e.target.closest('.chooser-card');
  if (!card) return;
  const mode = card.dataset.mode;
  if (!mode) return;
  setMode(mode);
  setView('hub');
  loadHub().catch(err => toast('Не удалось загрузить мифы: ' + err.message, 'error'));
});

function setupHubBindings() {
  // Фильтры
  document.querySelectorAll('.hub-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.hub-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.hubFilter = chip.dataset.filter;
      renderHubList();
    });
  });

  // Поиск
  const searchInput = $('scenario-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.hubSearchTerm = e.target.value.trim().toLowerCase();
      renderHubList();
    });
  }
}

async function loadHub() {
  try {
    state.summaries = await fetchJSON(api().myths);
  } catch (e) {
    toast('Не удалось загрузить список мифов: ' + e.message, 'error');
    return;
  }

  if (!state.summaries.length) {
    $('hub-list-items').innerHTML =
      `<div class="hub-list-empty">нет мифов ${state.mode === 'image' ? 'с картинками' : 'с озвучкой'}</div>`;
    $('hub-detail').innerHTML = '<div class="hub-empty">Нет данных</div>';
    return;
  }

  $('hub-count').textContent = String(state.summaries.length).padStart(2, '0');

  const preferred = state.summaries.find(s => s.status === 'in_progress')
                 || state.summaries[0];
  state.hubSelectedName = preferred.name;

  renderHubList();
  renderHubDetail();
}

function filterSummaries() {
  return state.summaries.filter(s => {
    if (state.hubFilter !== 'all' && s.status !== state.hubFilter) return false;
    if (state.hubSearchTerm &&
        !s.display_name.toLowerCase().includes(state.hubSearchTerm)) return false;
    return true;
  });
}

function statusLabel(status) {
  return {
    in_progress: 'в работе',
    ready: 'готов',
    new: 'новый',
    wip: 'wip',
  }[status] || status;
}

function statusSub(summary) {
  const { status, scene_count, done } = summary;
  if (status === 'wip') return 'материалы готовятся';
  if (status === 'new') return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · не начат`;
  if (status === 'ready') return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · готов к сборке`;
  return `${scene_count} сцен · ${done} проверено`;
}

function toRoman(num) {
  const map = [['M',1000],['CM',900],['D',500],['CD',400],['C',100],['XC',90],
               ['L',50],['XL',40],['X',10],['IX',9],['V',5],['IV',4],['I',1]];
  let res = '';
  for (const [r, v] of map) { while (num >= v) { res += r; num -= v; } }
  return res || '—';
}

function renderHubList() {
  const container = $('hub-list-items');
  const filtered = filterSummaries();

  if (!filtered.length) {
    container.innerHTML = '<div class="hub-list-empty">ничего не найдено</div>';
    return;
  }

  container.innerHTML = filtered.map((s) => {
    const globalIdx = state.summaries.findIndex(x => x.name === s.name);
    const active = s.name === state.hubSelectedName ? 'active' : '';
    const pct = s.scene_count ? (s.done / s.scene_count) * 100 : 0;

    const rightCol = s.status === 'in_progress'
      ? `<div class="hub-item-bar"><div class="hub-item-bar-fill" style="width:${pct}%"></div></div>`
      : `<div class="hub-item-status ${s.status}">${statusLabel(s.status)}</div>`;

    return `
      <div class="hub-item status-${s.status} ${active}" data-name="${escapeAttr(s.name)}">
        <div class="hub-item-num">${toRoman(globalIdx + 1)}</div>
        <div class="hub-item-body">
          <div class="hub-item-name">${escapeHtml(s.display_name)}</div>
          <div class="hub-item-sub">${escapeHtml(statusSub(s))}</div>
        </div>
        ${rightCol}
      </div>
    `;
  }).join('');

  container.querySelectorAll('.hub-item').forEach(el => {
    el.addEventListener('click', () => {
      state.hubSelectedName = el.dataset.name;
      renderHubList();
      renderHubDetail();
    });
    el.addEventListener('dblclick', () => {
      openScenarioReview(el.dataset.name);
    });
  });
}

async function renderHubDetail() {
  const container = $('hub-detail');
  const summary = state.summaries.find(s => s.name === state.hubSelectedName);

  if (!summary) {
    container.innerHTML = '<div class="hub-empty">Выберите миф слева</div>';
    return;
  }

  const globalIdx = state.summaries.findIndex(x => x.name === summary.name);
  const roman = toRoman(globalIdx + 1);
  const pct = summary.scene_count
    ? Math.round((summary.done / summary.scene_count) * 100)
    : 0;
  const durEstimate = summary.scene_count
    ? formatDuration(summary.scene_count * 2.5)
    : '—';

  const variantsPerScene = summary.scene_count
    ? (summary.variants_total / summary.scene_count).toFixed(1)
    : '0';

  const unitLabel = state.mode === 'image' ? 'кадров' : 'сцен';
  const durLabel = state.mode === 'image' ? 'сцен всего' : 'длительность';

  let ctaText, ctaBtnLabel;
  if (summary.status === 'wip') {
    ctaText = `<b>Материалы ещё готовятся.</b> ${state.mode === 'image' ? 'Картинки' : 'Озвучка'} для этого мифа пока не созданы.`;
    ctaBtnLabel = 'Открыть';
  } else if (summary.status === 'new') {
    ctaText = `<b>Ревью не начато.</b> ${summary.scene_count} сцен ждут проверки.`;
    ctaBtnLabel = 'Начать ревью';
  } else if (summary.status === 'ready') {
    ctaText = `<b>Все сцены проверены.</b> ${state.mode === 'image' ? 'Выбор сохранён.' : 'Можно собирать финальный трек.'}`;
    ctaBtnLabel = 'Открыть ревью';
  } else {
    const left = summary.pending + summary.regen;
    ctaText = `<b>Осталось проверить ${left} ${plural(left, 'сцену', 'сцены', 'сцен')}.</b>` +
              (summary.regen ? ` ${summary.regen} на перегенерацию.` : '');
    ctaBtnLabel = 'Продолжить ревью';
  }

  container.innerHTML = `
    <div class="hub-dp-eyebrow">
      <span>Миф · ${roman}</span>
      <span class="dossier-id">${escapeHtml(summary.name)}</span>
    </div>

    <h1 class="hub-dp-title">${escapeHtml(summary.display_name)}.</h1>
    <p class="hub-dp-subtitle">
      ${summary.scene_count
        ? `${summary.scene_count} ${plural(summary.scene_count, 'короткий кадр', 'коротких кадра', 'коротких кадров')} для ${state.mode === 'image' ? 'пиксель-арта' : 'озвучки'}.`
        : 'Сценарий в разработке.'}
    </p>

    <div class="hub-dp-stats">
      <div class="hub-dp-stat">
        <div class="hub-dp-stat-label">сцен всего</div>
        <div class="hub-dp-stat-value">${summary.scene_count}</div>
      </div>
      <div class="hub-dp-stat good">
        <div class="hub-dp-stat-label">проверено</div>
        <div class="hub-dp-stat-value">${summary.done}<span class="unit">/${summary.scene_count}</span></div>
      </div>
      <div class="hub-dp-stat accent">
        <div class="hub-dp-stat-label">варианты</div>
        <div class="hub-dp-stat-value">${summary.variants_total}<span class="unit">·${variantsPerScene}/сц.</span></div>
      </div>
      <div class="hub-dp-stat ${summary.regen ? 'warn' : ''}">
        <div class="hub-dp-stat-label">${summary.regen ? 'перегенерация' : durLabel}</div>
        <div class="hub-dp-stat-value">${summary.regen
          ? summary.regen
          : (state.mode === 'image'
             ? summary.scene_count
             : `<span style="font-size:0.9em">${durEstimate}</span>`)}</div>
      </div>
    </div>

    <div class="hub-dp-progress">
      <div class="hub-dp-progress-head">
        <div class="hub-dp-progress-label">прогресс ревью</div>
        <div class="hub-dp-progress-pct">${pct}%</div>
      </div>
      <div class="hub-dp-bar">
        <div class="hub-dp-bar-fill ${summary.status === 'ready' ? 'good' : ''}" style="width:${pct}%"></div>
      </div>
    </div>

    <div class="hub-dp-scenes-head">
      <div class="hub-dp-scenes-title">карта сцен</div>
      <div class="hub-dp-legend">
        <span><span class="dot done"></span>выбрано</span>
        <span><span class="dot regen"></span>перегенерация</span>
        <span><span class="dot pending"></span>ожидает</span>
      </div>
    </div>

    <div class="hub-dp-scenes" id="hub-scene-tiles">
      ${summary.scene_count
        ? `<div class="hub-list-loading" style="grid-column:1/-1">загрузка карты сцен…</div>`
        : `<div class="hub-list-empty" style="grid-column:1/-1">сцен нет</div>`}
    </div>

    <div class="hub-dp-cta">
      <div class="hub-dp-cta-text">${ctaText}</div>
      <button class="hub-btn hub-btn-primary" id="hub-open-btn" ${summary.status === 'wip' ? 'disabled' : ''}>
        ${ctaBtnLabel}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
      </button>
    </div>
  `;

  const openBtn = $('hub-open-btn');
  if (openBtn && summary.status !== 'wip') {
    openBtn.addEventListener('click', () => openScenarioReview(summary.name));
  }

  if (summary.scene_count > 0) {
    renderHubSceneTiles(summary.name);
  }
}

async function renderHubSceneTiles(scenario) {
  const tilesContainer = $('hub-scene-tiles');
  if (!tilesContainer) return;

  const ckey = cacheKey(scenario);
  let scenes = state.hubSceneCache[ckey];
  if (!scenes) {
    try {
      const data = await fetchJSON(api().scenes(scenario));
      scenes = data.scenes;
      state.hubSceneCache[ckey] = scenes;
    } catch (e) {
      tilesContainer.innerHTML =
        '<div class="hub-list-empty" style="grid-column:1/-1">ошибка загрузки сцен</div>';
      return;
    }
  }

  if (state.hubSelectedName !== scenario) return;

  tilesContainer.innerHTML = scenes.map(sc => {
    const cls = sc.status === 'done' ? 'done' : sc.status === 'regen' ? 'regen' : '';
    const num = sc.base.replace(/^[a-zA-Zа-яА-Я]+_0*/, '') || sc.base;
    return `<div class="hub-scene-tile ${cls}" title="${escapeAttr(sc.base)}${sc.text ? ': ' + escapeAttr(sc.text.slice(0, 60)) : ''}">${escapeHtml(num)}</div>`;
  }).join('');

  tilesContainer.querySelectorAll('.hub-scene-tile').forEach((tile, idx) => {
    tile.addEventListener('click', () => {
      openScenarioReview(scenario, scenes[idx].base);
    });
  });
}

async function openScenarioReview(scenario, targetSceneBase = null) {
  await loadScenario(scenario, targetSceneBase);
  setView('review');
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function escapeAttr(s) {
  return String(s || '').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

async function loadScenario(scenario, targetSceneBase = null) {
  state.scenario = scenario;
  scenarioTitle.textContent = scenario.replace(/_/g, ' ');
  const data = await fetchJSON(api().scenes(scenario));
  state.scenes = data.scenes;
  state.hubSceneCache[cacheKey(scenario)] = data.scenes;

  // Подтягиваем информацию о идущих/недавних генерациях CosyVoice,
  // чтобы сайдбар мог показать индикатор ещё до открытия сцены.
  if (state.mode === 'voice') {
    try {
      const active = await fetchJSON(
        `/api/cosyvoice-active/${encodeURIComponent(scenario)}`
      );
      for (const sc of state.scenes) {
        sc.cosy = active[sc.base] || null;
      }
    } catch (e) {
      console.warn('cosy-active failed', e);
    }
  }

  renderSidebar();
  updateStats();
  if (state.scenes.length) {
    const target = targetSceneBase && state.scenes.find(s => s.base === targetSceneBase)
      ? targetSceneBase
      : state.scenes[0].base;
    activateScene(target);
  }
  const summary = state.summaries.find(s => s.name === scenario);
  if (summary) {
    summary.done = state.scenes.filter(s => s.status === 'done').length;
    summary.regen = state.scenes.filter(s => s.status === 'regen').length;
    summary.pending = state.scenes.length - summary.done - summary.regen;
    if (summary.done === summary.scene_count && !summary.regen) summary.status = 'ready';
    else if (summary.done > 0 || summary.regen > 0) summary.status = 'in_progress';
    else summary.status = 'new';
  }
}

// ── Fetch helpers ─────────────────────────────────────────────────────────

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function postJSON(url, body) {
  return fetchJSON(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// ── Render sidebar ────────────────────────────────────────────────────────

function renderSidebar() {
  sceneNavList.innerHTML = state.scenes.map(scene => {
    const approvedClass = scene.approved ? 'approved' : '';
    const statusClass = scene.status === 'done' ? 'done'
                      : scene.status === 'regen' ? 'regen' : '';
    const active = scene.base === state.activeSceneBase ? 'active' : '';
    const preview = scene.text || '(нет текста)';
    const badge = scene.approved
      ? `<div class="nav-approved-badge" title="Одобрено — ${escapeHtml(scene.approved)}">★</div>`
      : '';

    // Маркер CosyVoice: показывает, что в этой сцене есть незавершённая
    // либо упавшая генерация. Пользователь видит статус прямо в списке,
    // без необходимости открывать каждую сцену.
    let cosyBadge = '';
    if (scene.cosy && !scene.cosy.done) {
      const mod = scene.cosy.failed ? 'failed' : 'running';
      const title = scene.cosy.failed
        ? 'CosyVoice упал — открой сцену, чтобы увидеть лог'
        : `CosyVoice генерирует: ${scene.cosy.produced}/${scene.cosy.requested}`;
      cosyBadge = `<div class="nav-cosy-badge ${mod}" title="${escapeAttr(title)}">
          ${scene.cosy.failed ? '!' : `${scene.cosy.produced}/${scene.cosy.requested}`}
        </div>`;
    }

    return `
      <div class="scene-nav-item ${approvedClass} ${statusClass} ${active}" data-base="${scene.base}">
        <div class="nav-indicator"></div>
        <div class="nav-num">${scene.base.replace('scene_', '')}</div>
        <div class="nav-text" title="${escapeHtml(preview)}">${escapeHtml(preview)}</div>
        ${cosyBadge}
        ${badge}
      </div>
    `;
  }).join('');

  sceneNavList.querySelectorAll('.scene-nav-item').forEach(el => {
    el.addEventListener('click', () => activateScene(el.dataset.base));
  });
}

// ── Render scene detail ───────────────────────────────────────────────────

function activateScene(base) {
  if (state.cosy.base && state.cosy.base !== base) {
    stopCosyProgress();
  }
  state.activeSceneBase = base;
  stopAudio();
  sceneNavList.querySelectorAll('.scene-nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.base === base);
  });

  const scene = state.scenes.find(s => s.base === base);
  if (!scene) return;

  emptyState.style.display = 'none';
  sceneDetail.style.display = '';

  const idx = state.scenes.findIndex(s => s.base === base);
  const prevDisabled = idx <= 0 ? 'disabled' : '';
  const nextDisabled = idx >= state.scenes.length - 1 ? 'disabled' : '';

  const isImage = state.mode === 'image';
  const textHeader = isImage ? 'Текст сцены' : 'Текст для озвучки';
  const variantsHeader = isImage ? 'Варианты изображений' : 'Варианты озвучки';

  // Блок с текстом: в режиме image добавляем рядом промпт
  const textSection = isImage && scene.prompt
    ? `
      <div class="text-grid">
        <div class="text-block">
          <div class="text-block-header">${textHeader}</div>
          <div class="text-block-content">${escapeHtml(scene.text || '(нет текста)')}</div>
        </div>
        <div class="text-block prompt-block">
          <div class="text-block-header">Промпт</div>
          <div class="text-block-content">${escapeHtml(scene.prompt)}</div>
        </div>
      </div>
    `
    : `
      <div class="text-block">
        <div class="text-block-header">${textHeader}</div>
        <div class="text-block-content">${escapeHtml(scene.text || '(нет текста)')}</div>
      </div>
    `;

  // Regen-bar: в режиме image убираем кнопку ElevenLabs
  const regenBar = isImage
    ? `
      <div class="regen-bar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f55b5b" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
        <div class="regen-bar-text">Ни один вариант не подходит?</div>
        <button class="regen-bar-btn" id="regen-btn">Пометить на перегенерацию</button>
      </div>
    `
    : `
      <div class="regen-bar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f55b5b" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
        <div class="regen-bar-text">Ни один вариант не подходит?</div>
        <button class="regen-bar-btn" id="regen-btn">Перегенерировать</button>
        <button class="regen-bar-btn-hard" id="regen-11-btn" title="Запустить озвучку прямо сейчас">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          Перегенерировать в Elevenlabs
        </button>
      </div>
    `;

  sceneDetail.innerHTML = `
    <div class="detail-header">
      <div class="detail-title">
        <div class="detail-num">${scene.base.replace('scene_', '')}</div>
        <div><div class="detail-label">Сцена</div></div>
      </div>
      <div class="detail-nav">
        <button class="nav-arrow" id="nav-prev" ${prevDisabled}>&larr;</button>
        <button class="nav-arrow" id="nav-next" ${nextDisabled}>&rarr;</button>
      </div>
    </div>

    ${textSection}

    <div>
      <div class="variants-section-header">
        <h2>${variantsHeader}</h2>
        <div class="variant-count">${scene.variants.length} ${plural(scene.variants.length, 'вариант', 'варианта', 'вариантов')}</div>
      </div>
    </div>

    <div class="variants-grid">
      ${scene.variants.map(v => renderVariantCard(scene, v)).join('')}
    </div>

    ${regenBar}
  `;

  if (isImage) {
    sceneDetail.querySelectorAll('.variant-card.is-image').forEach(attachImageVariantHandlers);
  } else {
    sceneDetail.querySelectorAll('.variant-card').forEach(attachVariantHandlers);
  }
  $('regen-btn').addEventListener('click', () => onRegenerate(base));
  const regen11 = $('regen-11-btn');
  if (regen11) regen11.addEventListener('click', () => onRegenerateElevenLabs(base));
  $('nav-prev').addEventListener('click', () => navigateScene(-1));
  $('nav-next').addEventListener('click', () => navigateScene(1));

  // Восстановление прогресса CosyVoice после перезагрузки страницы.
  // Источник истины — файлы на диске (log + report), опрашиваем их один раз;
  // если runner ещё работает / упал без отчёта — подхватываем прогресс-бар.
  if (!isImage) {
    resumeCosyIfActive(base).catch(err => console.warn('cosy resume', err));
  }
}

function renderVariantCard(scene, variant) {
  if (state.mode === 'image') return renderImageCard(scene, variant);
  return renderAudioCard(scene, variant);
}

function renderAudioCard(scene, variant) {
  const isApproved = scene.approved === variant.variant;
  const isChosen = scene.selected === variant.variant;
  const classes = [
    'variant-card',
    isApproved ? 'approved' : '',
    isChosen ? 'chosen' : '',
  ].filter(Boolean).join(' ');
  const audioPath = (variant.path || variant.filename)
    .split('/')
    .map(encodeURIComponent)
    .join('/');
  const audioUrl = `/audio/${encodeURIComponent(state.scenario)}/${audioPath}`;
  const btnLabel = isApproved
    ? '★ Одобрено'
    : isChosen ? '✓ Выбрано' : 'Выбрать';
  return `
    <div class="${classes}" data-base="${scene.base}" data-variant="${variant.variant}" data-audio="${audioUrl}">
      <div class="variant-top">
        <div class="v-play"><svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21" class="play-icon"/></svg></div>
        <div class="v-info">
          <div class="v-name">${escapeHtml(variant.filename)}</div>
          <div class="v-meta">ElevenLabs &middot; вариант ${variant.variant}</div>
        </div>
      </div>
      <div class="v-audio-wrap">
        <div class="v-progress"><div class="v-progress-fill"></div></div>
        <div class="v-time"><span class="v-cur">00:00</span><span class="v-dur">00:00</span></div>
      </div>
      <div class="v-actions">
        <div class="v-filesize">${variant.size_kb} КБ</div>
        <button class="v-select-btn">${btnLabel}</button>
      </div>
    </div>
  `;
}

function renderImageCard(scene, variant) {
  const isChosen = scene.selected === variant.variant;
  const classes = [
    'variant-card', 'is-image',
    isChosen ? 'chosen' : '',
  ].filter(Boolean).join(' ');
  const imgUrl = `/image/${encodeURIComponent(state.scenario)}/${encodeURIComponent(scene.base)}/${encodeURIComponent(variant.filename)}`;
  const btnLabel = isChosen ? '✓ Выбрано' : 'Выбрать';
  return `
    <div class="${classes}" data-base="${scene.base}" data-variant="${variant.variant}">
      <div class="v-image">
        <img src="${imgUrl}" alt="${escapeAttr(variant.filename)}" loading="lazy">
        <span class="v-image-badge">${escapeHtml(variant.variant)}</span>
        <span class="v-image-size">${variant.size_kb} КБ</span>
      </div>
      <div class="v-actions">
        <div class="v-filesize">${escapeHtml(variant.filename)}</div>
        <button class="v-select-btn">${btnLabel}</button>
      </div>
    </div>
  `;
}

function attachVariantHandlers(card) {
  if (card.classList.contains('is-image')) return;  // image-карточки идут в attachImageVariantHandlers
  const playBtn = card.querySelector('.v-play');
  const selectBtn = card.querySelector('.v-select-btn');
  const progress = card.querySelector('.v-progress');
  const fill = card.querySelector('.v-progress-fill');
  const curLabel = card.querySelector('.v-cur');
  const durLabel = card.querySelector('.v-dur');

  playBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePlay(card, fill, curLabel, durLabel);
  });

  progress.addEventListener('click', (e) => {
    if (state.currentPlayingCard === card && state.currentAudio) {
      const rect = progress.getBoundingClientRect();
      const ratio = (e.clientX - rect.left) / rect.width;
      state.currentAudio.currentTime = ratio * state.currentAudio.duration;
    }
  });

  selectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    onSelectVariant(card.dataset.base, card.dataset.variant);
  });
}

function attachImageVariantHandlers(card) {
  const img = card.querySelector('.v-image img');
  const selectBtn = card.querySelector('.v-select-btn');

  if (img) {
    img.addEventListener('click', (e) => {
      e.stopPropagation();
      openLightbox(img.src, card.dataset.base, card.dataset.variant);
    });
  }

  selectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    onSelectVariant(card.dataset.base, card.dataset.variant);
  });
}

// ── Audio playback ────────────────────────────────────────────────────────

function togglePlay(card, fill, curLabel, durLabel) {
  const audioUrl = card.dataset.audio;

  if (state.currentPlayingCard === card && state.currentAudio && !state.currentAudio.paused) {
    state.currentAudio.pause();
    updatePlayIcon(card, false);
    return;
  }

  stopAudio();

  const audio = new Audio(audioUrl);
  state.currentAudio = audio;
  state.currentPlayingCard = card;

  card.classList.add('playing');
  updatePlayIcon(card, true);

  audio.addEventListener('loadedmetadata', () => {
    durLabel.textContent = formatTime(audio.duration);
  });

  audio.addEventListener('timeupdate', () => {
    const ratio = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
    fill.style.width = ratio + '%';
    curLabel.textContent = formatTime(audio.currentTime);
  });

  audio.addEventListener('ended', () => {
    updatePlayIcon(card, false);
    fill.style.width = '0%';
    curLabel.textContent = '00:00';
    card.classList.remove('playing');
    state.currentAudio = null;
    state.currentPlayingCard = null;
  });

  audio.addEventListener('error', () => {
    toast('Не удалось загрузить аудио', 'error');
    card.classList.remove('playing');
    updatePlayIcon(card, false);
  });

  audio.play();
}

function stopAudio() {
  if (state.currentAudio) {
    state.currentAudio.pause();
    state.currentAudio = null;
  }
  if (state.currentPlayingCard) {
    state.currentPlayingCard.classList.remove('playing');
    updatePlayIcon(state.currentPlayingCard, false);
    const fill = state.currentPlayingCard.querySelector('.v-progress-fill');
    if (fill) fill.style.width = '0%';
    state.currentPlayingCard = null;
  }
}

function updatePlayIcon(card, playing) {
  const icon = card.querySelector('.play-icon');
  if (!icon) return;
  if (playing) {
    icon.setAttribute('points', '6,4 10,4 10,20 6,20 14,4 18,4 18,20 14,20');
  } else {
    icon.setAttribute('points', '5,3 19,12 5,21');
  }
}

function formatTime(sec) {
  if (!isFinite(sec)) return '00:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ── Lightbox (только для изображений) ────────────────────────────────────

function openLightbox(src, base, variant) {
  let lb = $('image-lightbox');
  if (!lb) {
    lb = document.createElement('div');
    lb.id = 'image-lightbox';
    lb.className = 'image-lightbox';
    lb.innerHTML = `
      <div class="image-lightbox-info"></div>
      <button class="image-lightbox-close">✕ Esc</button>
      <img alt="">
    `;
    document.body.appendChild(lb);
    lb.addEventListener('click', (e) => {
      if (e.target === lb || e.target.classList.contains('image-lightbox-close')) {
        closeLightbox();
      }
    });
  }
  lb.querySelector('img').src = src;
  lb.querySelector('.image-lightbox-info').textContent =
    `${base} · вариант ${variant}`;
  lb.classList.add('show');
}

function closeLightbox() {
  const lb = $('image-lightbox');
  if (lb) lb.classList.remove('show');
}

// ── Actions ──────────────────────────────────────────────────────────────

async function onSelectVariant(base, variant) {
  const scene = state.scenes.find(s => s.base === base);
  if (!scene) return;

  const newVariant = scene.selected === variant ? null : variant;

  try {
    await postJSON(api().select(state.scenario), { base, variant: newVariant });
    scene.selected = newVariant;
    scene.status = newVariant ? 'done' : 'pending';

    updateVariantCardsUI(base, newVariant);
    updateSidebarItem(base, scene.status);
    updateStats();
  } catch (e) {
    toast('Не удалось сохранить выбор: ' + e.message, 'error');
  }
}

function updateVariantCardsUI(base, selectedVariant) {
  const scene = state.scenes.find(s => s.base === base);
  const approvedVariant = scene ? scene.approved : null;
  const cards = sceneDetail.querySelectorAll(`.variant-card[data-base="${CSS.escape(base)}"]`);
  cards.forEach(card => {
    const v = card.dataset.variant;
    const isChosen = v === selectedVariant;
    const isApproved = v === approvedVariant;
    card.classList.toggle('chosen', isChosen);
    card.classList.toggle('approved', isApproved);
    const btn = card.querySelector('.v-select-btn');
    if (btn) {
      btn.textContent = isApproved ? '\u2605 Одобрено'
                      : isChosen ? '\u2713 Выбрано' : 'Выбрать';
    }
  });
}

function updateSidebarItem(base, status) {
  const el = sceneNavList.querySelector(`.scene-nav-item[data-base="${CSS.escape(base)}"]`);
  if (!el) return;
  el.classList.remove('done', 'regen');
  if (status === 'done') el.classList.add('done');
  else if (status === 'regen') el.classList.add('regen');
}

function updateSidebarCosyBadge(base, cosy) {
  const el = sceneNavList.querySelector(`.scene-nav-item[data-base="${CSS.escape(base)}"]`);
  if (!el) return;
  const existing = el.querySelector('.nav-cosy-badge');
  if (!cosy || cosy.done) {
    if (existing) existing.remove();
    return;
  }
  const mod = cosy.failed ? 'failed' : 'running';
  const label = cosy.failed ? '!' : `${cosy.produced}/${cosy.requested}`;
  const title = cosy.failed
    ? 'CosyVoice упал — открой сцену, чтобы увидеть лог'
    : `CosyVoice генерирует: ${cosy.produced}/${cosy.requested}`;
  if (existing) {
    existing.className = `nav-cosy-badge ${mod}`;
    existing.textContent = label;
    existing.title = title;
  } else {
    const badge = document.createElement('div');
    badge.className = `nav-cosy-badge ${mod}`;
    badge.textContent = label;
    badge.title = title;
    // Вставляем перед approved-badge, если он есть, иначе в конец
    const approvedBadge = el.querySelector('.nav-approved-badge');
    if (approvedBadge) el.insertBefore(badge, approvedBadge);
    else el.appendChild(badge);
  }
}

async function onRegenerate(base) {
  const isImage = state.mode === 'image';

  // Voice-режим: CosyVoice3 zero-shot c клонированием голоса.
  // Параметры жёстко зафиксированы пользователем: 10 вариантов, скорость 1.1,
  // prompt-wav = content/Ящик Пандоры/TTS.mp3, prompt-text = TTS.txt.
  const cosyParams = {
    model: 'Fun-CosyVoice3-0.5B',
    variants: 10,
    speed: 1.1,
    promptWav: 'content/Ящик Пандоры/TTS.mp3',
    promptTxt: 'content/Ящик Пандоры/TTS.txt',
  };

  const cosyBody = `
    Сцена <b>${escapeHtml(base)}</b> будет заново озвучена моделью
    <b>${cosyParams.model}</b>.
    <div class="mb-stats" style="margin-top:12px">
      <div class="mb-stat"><span class="mb-stat-label">Модель</span><span class="mb-stat-num">CosyVoice3</span></div>
      <div class="mb-stat"><span class="mb-stat-label">Вариантов</span><span class="mb-stat-num">${cosyParams.variants}</span></div>
      <div class="mb-stat"><span class="mb-stat-label">Скорость</span><span class="mb-stat-num">${cosyParams.speed}</span></div>
    </div>
    <div class="mb-note" style="margin-top:10px">
      Клонирование голоса из <code>${escapeHtml(cosyParams.promptWav)}</code>,
      транскрипт <code>${escapeHtml(cosyParams.promptTxt)}</code>.
      Варианты сгенерируются асинхронно — UI не блокируется.
    </div>
  `;

  const ok = await showModal({
    title: isImage ? 'Пометить на перегенерацию?' : 'Перегенерировать через CosyVoice 3',
    bodyHtml: isImage
      ? `Сцена <b>${escapeHtml(base)}</b> попадёт в список на перегенерацию. ` +
        `Картинки будут сгенерированы заново через <code>imagefx_runner.py</code>.`
      : cosyBody,
    confirmText: isImage ? 'Пометить' : 'Запустить CosyVoice',
    danger: true,
  });
  if (!ok) return;

  try {
    const res = await postJSON(api().regen(state.scenario), { base });

    // В voice-режиме выводим параметры озвучки уведомлением (как попросил пользователь).
    if (!isImage) {
      const parts = [
        `Модель: ${res.model || cosyParams.model}`,
        `Вариантов: ${res.variants ?? cosyParams.variants}`,
        `Скорость: ${res.speed ?? cosyParams.speed}`,
        `Prompt: ${res.prompt_wav || cosyParams.promptWav}`,
      ];
      if (res.pid) parts.push(`PID: ${res.pid}`);
      toast('CosyVoice 3 запущен · ' + parts.join(' · '), 'success');
    } else {
      toast(res.message || 'Сцена отправлена на перегенерацию', 'success');
    }

    const scene = state.scenes.find(s => s.base === base);
    if (scene) {
      scene.selected = null;
      scene.status = 'regen';
    }
    updateVariantCardsUI(base, null);
    updateSidebarItem(base, 'regen');
    updateStats();

    // Voice-режим: запускаем поллинг прогресса CosyVoice3
    if (!isImage) {
      startCosyProgress(base, {
        requested: res.variants ?? cosyParams.variants,
        model: res.model || cosyParams.model,
        speed: res.speed ?? cosyParams.speed,
        promptWav: res.prompt_wav || cosyParams.promptWav,
      });
    }
  } catch (e) {
    toast('Ошибка: ' + e.message, 'error');
  }
}

// ── CosyVoice progress polling ────────────────────────────────────────────

// Дефолтные параметры — совпадают с тем, что backend использует по умолчанию.
// Нужны при восстановлении прогресса после перезагрузки страницы, когда
// мета из ответа /api/regenerate-cosyvoice уже недоступна.
const COSY_DEFAULT_META = {
  model: 'Fun-CosyVoice3-0.5B',
  requested: 10,
  speed: 1.1,
  promptWav: 'content/Ящик Пандоры/TTS.mp3',
};

async function resumeCosyIfActive(base) {
  // Уже активно поллим эту сцену — ничего не делаем
  if (state.cosy.base === base && state.cosy.timer) return;
  // Не дёргаем лишний раз, если генерация в другой сцене идёт
  if (state.cosy.base && state.cosy.base !== base) return;

  let status;
  try {
    const url = `/api/cosyvoice-status/${encodeURIComponent(state.scenario)}/${encodeURIComponent(base)}`;
    status = await fetchJSON(url);
  } catch (e) {
    return;
  }
  if (!status || !status.exists) return;

  // Логов нет — генерацию никто не запускал. Тихо уходим.
  if (!status.log_tail) return;

  // Успешно завершено и все файлы на месте — отдельный прогресс-бар не нужен,
  // новые варианты и так лежат в карточках. Но если runner упал (report=null),
  // пусть пользователь увидит панель с логом и маркером ошибки.
  const finishedClean = status.done
    && status.report
    && (status.report.variants_produced || 0) >= (status.report.variants_requested || 0);
  if (finishedClean) return;

  // Прошёл >20 секунд с последнего апдейта лога и report нет — считаем
  // generation «повисшей» или упавшей. Всё равно покажем панель — startCosy
  // сам через маркеры в tail определит failed-статус.
  startCosyProgress(base, { ...COSY_DEFAULT_META });
}


function startCosyProgress(base, meta) {
  stopCosyProgress();
  state.cosy.base = base;
  state.cosy.meta = meta;
  state.cosy.startedAt = Date.now();
  state.cosy.lastProduced = 0;
  state.cosy.lastProducedAt = Date.now();
  state.cosy.autoOpenedOnFail = false;
  // Первый раз рисуем каркас, дальше обновляем inline — чтобы <details> и <pre>
  // не пересоздавались и пользовательский scroll / open-state не терялись.
  mountCosyProgress(base, meta);
  updateCosyProgress(base, meta, {
    exists: true, done: false, produced: 0,
    requested: meta.requested, log_tail: 'запуск runner…', error_hint: null,
  });

  const tick = async () => {
    if (state.cosy.base !== base) return;  // пользователь ушёл на другую сцену
    try {
      const url = `/api/cosyvoice-status/${encodeURIComponent(state.scenario)}/${encodeURIComponent(base)}`;
      const status = await fetchJSON(url);
      if (state.cosy.base !== base) return;

      // Детектим «зависание»: прогресса нет >60 сек и уже видна ошибка в логе
      const now = Date.now();
      if (status.produced > state.cosy.lastProduced) {
        state.cosy.lastProduced = status.produced;
        state.cosy.lastProducedAt = now;
      }
      const stalledSec = (now - state.cosy.lastProducedAt) / 1000;
      // Backend теперь сам флагает ошибку маркерами в tail лога + silence >30с.
      // Если backend сказал error_hint — доверяем сразу (кроме случая, когда
      // варианты уже идут: тогда это просто старый лог прошлого запуска).
      const failed = !status.done && !!status.error_hint && status.produced === 0;

      updateCosyProgress(base, state.cosy.meta || meta, status, { stalledSec, failed });

      // Обновляем в сайдбаре счётчик по ходу генерации
      const sc = state.scenes.find(s => s.base === base);
      if (sc) {
        sc.cosy = {
          done: status.done,
          produced: status.produced,
          requested: status.requested,
          failed: !!(status.error_hint && stalledSec > 20 && status.produced === 0),
        };
        updateSidebarCosyBadge(base, sc.cosy);
      }

      if (status.done) {
        stopCosyProgress();
        toast(
          `CosyVoice 3: готово ${status.report?.variants_produced ?? status.produced}/${status.requested}`,
          'success',
        );
        // Перезагружаем сценарий, чтобы подтянуть новые варианты в карточки
        await loadScenario(state.scenario, base);
        return;
      }
      if (failed) {
        stopCosyProgress();
        toast(
          `CosyVoice 3: runner упал (${status.error_hint}). Смотри лог в прогресс-панели.`,
          'error',
        );
      }
    } catch (e) {
      console.warn('cosy poll error', e);
    }
  };

  tick();
  state.cosy.timer = setInterval(tick, 1500);
}

function stopCosyProgress() {
  if (state.cosy.timer) clearInterval(state.cosy.timer);
  state.cosy.timer = null;
  state.cosy.base = null;
}

// Разделили рендер на mount (один раз — строим DOM) и update (точечные
// обновления внутренних узлов). Раньше innerHTML пересоздавал <details>
// на каждом тике — пользовательский клик «открыть лог» терялся и элемент
// схлопывался. Теперь узлы живут между тиками.
function mountCosyProgress(base, meta) {
  if (state.activeSceneBase !== base) return;
  const bar = sceneDetail.querySelector('.regen-bar');
  if (!bar) return;

  bar.className = 'regen-bar cosy-progress cosy-running';
  bar.innerHTML = `
    <div class="cosy-head">
      <div class="cosy-title"></div>
      <div class="cosy-count"></div>
      <button class="cosy-reset-btn" title="Удалить лог и report" style="display:none">Сбросить</button>
    </div>
    <div class="cosy-bar"><div class="cosy-bar-fill" style="width:0%"></div></div>
    <div class="cosy-meta"></div>
    <details class="cosy-log">
      <summary></summary>
      <pre></pre>
    </details>
    <div class="cosy-log-empty" style="display:none"></div>
  `;

  // Сбрасывает статус сцены в чистое состояние — нужно когда runner в прошлом
  // упал, лог остался, а новая генерация не запускалась, но UI всё равно
  // рисует красный бейдж.
  bar.querySelector('.cosy-reset-btn').addEventListener('click', async () => {
    try {
      await postJSON(
        `/api/cosyvoice-clear/${encodeURIComponent(state.scenario)}/${encodeURIComponent(base)}`,
        {},
      );
      stopCosyProgress();
      const sc = state.scenes.find(s => s.base === base);
      if (sc) {
        sc.cosy = null;
        if (sc.status === 'regen') sc.status = 'pending';
      }
      toast('Статус CosyVoice сброшен', 'success');
      // Перерисовываем сайдбар + правую панель
      updateSidebarCosyBadge(base, null);
      updateSidebarItem(base, sc ? sc.status : 'pending');
      activateScene(base);
    } catch (e) {
      toast('Не удалось сбросить: ' + e.message, 'error');
    }
  });

  const details = bar.querySelector('.cosy-log');
  const pre = details.querySelector('pre');

  // Пользователь открыл/закрыл — запоминаем, чтобы следующий тик не откатил.
  details.addEventListener('toggle', () => {
    state.cosy.logOpen = details.open;
    if (details.open) {
      // При первом раскрытии прокручиваем в конец и «приклеиваемся»
      pre.scrollTop = pre.scrollHeight;
      state.cosy.logScrollPinnedBottom = true;
    }
  });

  // Если юзер сам проскроллил лог выше — не прыгаем ему назад в конец.
  pre.addEventListener('scroll', () => {
    const atBottom = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 4;
    state.cosy.logScrollPinnedBottom = atBottom;
  });
}

function updateCosyProgress(base, meta, status, flags = {}) {
  if (state.activeSceneBase !== base) return;
  const bar = sceneDetail.querySelector('.regen-bar');
  if (!bar || !bar.classList.contains('cosy-progress')) {
    // Каркас могли затереть — монтируем ещё раз.
    mountCosyProgress(base, meta);
    if (!sceneDetail.querySelector('.regen-bar.cosy-progress')) return;
  }

  const root = sceneDetail.querySelector('.regen-bar');
  const requested = status.requested || meta.requested || 10;
  const produced = status.produced || 0;
  const pct = requested ? Math.min(100, Math.round((produced / requested) * 100)) : 0;
  const elapsedSec = Math.max(0, Math.round((Date.now() - state.cosy.startedAt) / 1000));

  const headline = status.done
    ? `CosyVoice 3 · готово`
    : flags.failed
      ? `CosyVoice 3 · ошибка`
      : produced === 0
        ? `CosyVoice 3 · прогрев модели…`
        : `CosyVoice 3 · генерирую варианты`;

  const statusClass = status.done ? 'done' : flags.failed ? 'failed' : 'running';
  root.className = `regen-bar cosy-progress cosy-${statusClass}`;

  root.querySelector('.cosy-title').textContent = headline;
  root.querySelector('.cosy-count').textContent = `${produced}/${requested}`;
  root.querySelector('.cosy-bar-fill').style.width = `${pct}%`;

  // Кнопка «Сбросить» видна всегда — пользователь сам решит, надо ли сносить.
  // Аккуратно: при активной генерации нажатие уничтожит лог, но сам процесс
  // в venv продолжит работать и создаст новый лог на следующем писании.
  const resetBtn = root.querySelector('.cosy-reset-btn');
  if (resetBtn) resetBtn.style.display = '';

  const metaLine = [
    `модель ${meta.model}`,
    `скорость ${meta.speed}`,
    `prompt ${meta.promptWav}`,
  ].join(' · ');
  root.querySelector('.cosy-meta').textContent = metaLine;

  const details = root.querySelector('.cosy-log');
  const summary = details.querySelector('summary');
  const pre = details.querySelector('pre');
  const empty = root.querySelector('.cosy-log-empty');

  if (status.log_tail) {
    details.style.display = '';
    empty.style.display = 'none';
    summary.textContent = `лог runner (${elapsedSec}с)`;

    // При ошибке — один раз принудительно раскрываем лог. Дальше решает юзер.
    if (flags.failed && !state.cosy.autoOpenedOnFail) {
      details.open = true;
      state.cosy.logOpen = true;
      state.cosy.autoOpenedOnFail = true;
    } else {
      // Во всех остальных случаях уважаем последний выбор пользователя.
      details.open = state.cosy.logOpen;
    }

    const newTail = status.log_tail.slice(-4000);
    if (pre.textContent !== newTail) {
      pre.textContent = newTail;
      // Автоскролл только если пользователь не листал вверх.
      if (state.cosy.logScrollPinnedBottom) {
        pre.scrollTop = pre.scrollHeight;
      }
    }
  } else {
    details.style.display = 'none';
    empty.style.display = '';
    empty.textContent = `лог пока пуст (${elapsedSec}с)`;
  }
}

async function onRegenerateElevenLabs(base) {
  const ok = await showModal({
    title: 'Прямая перегенерация через ElevenLabs',
    bodyHtml: `Запустить озвучку сцены <b>${escapeHtml(base)}</b> прямо сейчас? ` +
              `Скрипт обратится к ElevenLabs API и сгенерирует новые варианты в папку <code>review_sentences</code>.`,
    confirmText: 'Запустить',
    danger: true,
  });
  if (!ok) return;

  try {
    const res = await postJSON(
      api().regenEL(state.scenario),
      { base }
    );
    toast(res.message || 'Запрос отправлен в ElevenLabs', 'success');
  } catch (e) {
    toast('Ошибка: ' + e.message, 'error');
  }
}

async function onFinalize() {
  const done = state.scenes.filter(s => s.status === 'done').length;
  const regen = state.scenes.filter(s => s.status === 'regen').length;
  const pending = state.scenes.filter(s => s.status === 'pending').length;

  const isImage = state.mode === 'image';
  const targetFolder = isImage ? 'approved_images' : 'approved_sentences';
  const what = isImage ? 'картинки' : 'озвучки';

  const note = pending > 0
    ? `<div class="mb-note">${pending} сцен без выбора — останутся нетронутыми, можно вернуться к ним позже.</div>`
    : '';

  const bodyHtml = `
    Выбранные ${what} будут скопированы в <code>${targetFolder}</code>.
    <div class="mb-stats">
      <div class="mb-stat"><span class="mb-stat-icon g"></span><span class="mb-stat-label">Выбрано</span><span class="mb-stat-num">${done}</span></div>
      <div class="mb-stat"><span class="mb-stat-icon r"></span><span class="mb-stat-label">На перегенерацию</span><span class="mb-stat-num">${regen}</span></div>
    </div>
    ${note}
  `;

  const ok = await showModal({
    title: 'Собрать финал',
    bodyHtml,
    confirmText: 'Собрать',
  });
  if (!ok) return;

  try {
    const res = await postJSON(api().finalize(state.scenario), {});
    let msg = `Скопировано ${res.copied_count} файлов в ${res.approved_dir}. На перегенерацию: ${res.regen_count}.`;
    let toastType = 'success';
    if (res.full_audio) {
      msg += ` Склейка: ${res.full_audio}.`;
    } else if (res.concat_error) {
      msg += ` Склейка не удалась: ${res.concat_error}.`;
      toastType = 'error';
    }
    toast(msg, toastType);
    await loadScenario(state.scenario);
  } catch (e) {
    toast('Ошибка: ' + e.message, 'error');
  }
}

function navigateScene(delta) {
  const idx = state.scenes.findIndex(s => s.base === state.activeSceneBase);
  const next = idx + delta;
  if (next < 0 || next >= state.scenes.length) return;
  activateScene(state.scenes[next].base);
}

// ── Stats & progress ─────────────────────────────────────────────────────

function updateStats() {
  const done = state.scenes.filter(s => s.status === 'done').length;
  const regen = state.scenes.filter(s => s.status === 'regen').length;
  const pending = state.scenes.filter(s => s.status === 'pending').length;
  const total = state.scenes.length;

  $('stat-done').textContent = done;
  $('stat-regen').textContent = regen;
  $('stat-pending').textContent = pending;
  $('done-count').textContent = done;
  $('total-count').textContent = total;

  const circumference = 2 * Math.PI * 10;
  const ratio = total ? (done + regen) / total : 0;
  $('ring-fill').style.strokeDashoffset = circumference * (1 - ratio);
}

// ── Utils ────────────────────────────────────────────────────────────────

function plural(n, one, few, many) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s || '';
  return div.innerHTML;
}

let toastTimer = null;
function toast(msg, type = '') {
  toastEl.textContent = msg;
  toastEl.className = 'toast show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.className = 'toast ' + type;
  }, 3500);
}

// ── Кастомная модалка (замена confirm) ──
function showModal({ title, bodyHtml, confirmText = 'OK', cancelText = 'Отмена', danger = false }) {
  return new Promise(resolve => {
    const modal = $('modal');
    $('modal-title').textContent = title;
    $('modal-body').innerHTML = bodyHtml;

    const confirmBtn = $('modal-confirm');
    const cancelBtn = $('modal-cancel');
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;
    confirmBtn.className = 'modal-btn ' + (danger ? 'modal-btn-danger' : 'modal-btn-primary');

    const close = (value) => {
      modal.classList.remove('show');
      confirmBtn.onclick = null;
      cancelBtn.onclick = null;
      modal.onclick = null;
      document.removeEventListener('keydown', onKey);
      resolve(value);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); close(false); }
      if (e.key === 'Enter') { e.preventDefault(); close(true); }
    };

    confirmBtn.onclick = () => close(true);
    cancelBtn.onclick = () => close(false);
    modal.onclick = (e) => { if (e.target === modal) close(false); };
    document.addEventListener('keydown', onKey);
    modal.classList.add('show');
    confirmBtn.focus();
  });
}

// ── Keyboard ─────────────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  // Lightbox: Esc закрывает
  const lb = $('image-lightbox');
  if (lb && lb.classList.contains('show')) {
    if (e.key === 'Escape') { closeLightbox(); e.preventDefault(); }
    return;
  }

  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (document.body.dataset.view !== 'review') return;

  if (e.key === 'ArrowDown' || e.key === 'j') { navigateScene(1); e.preventDefault(); }
  if (e.key === 'ArrowUp' || e.key === 'k') { navigateScene(-1); e.preventDefault(); }

  if (state.mode === 'voice' && e.key === ' ') {
    const firstCard = sceneDetail.querySelector('.variant-card');
    if (firstCard) {
      firstCard.querySelector('.v-play')?.click();
      e.preventDefault();
    }
  }

  // В режиме image: 1/2/3/4 — выбрать N-й вариант
  if (state.mode === 'image' && ['1','2','3','4'].includes(e.key)) {
    const scene = state.scenes.find(s => s.base === state.activeSceneBase);
    if (!scene) return;
    const idx = parseInt(e.key) - 1;
    const variant = scene.variants[idx];
    if (variant) {
      onSelectVariant(scene.base, variant.variant);
      e.preventDefault();
    }
  }
});

// Init
$('finalize-btn').addEventListener('click', onFinalize);
init().catch(e => toast('Ошибка инициализации: ' + e.message, 'error'));
