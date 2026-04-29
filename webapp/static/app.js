// State
const state = {
  mode: 'voice',   // 'voice' | 'image' | 'video'
  scenario: null,
  scenes: [],
  activeSceneBase: null,
  currentAudio: null,
  currentPlayingCard: null,
  currentPlayingVideo: null,    // активный <video> элемент в video-режиме
  // Hub
  summaries: [],
  hubSelectedName: null,
  hubFilter: 'all',
  hubSceneCache: {},   // key: `${mode}::${scenario}`
  hubSearchTerm: '',
  // Публикация (общий флаг per-scenario, разделяемый между режимами).
  // Поддерживается в актуальном состоянии для активного сценария ревью —
  // bottombar-кнопка читает отсюда.
  scenarioPublished: false,
  scenarioPublishedAt: null,
  // Кросс-модовая статистика для rail (быстрый переключатель режимов).
  // Заполняется в loadScenario одним залпом (3 параллельных запроса /myths)
  // и обновляется при возврате в review. По каждому режиму храним done/total/
  // exists, чтобы rail мог нарисовать кольцо прогресса и точку «нов».
  modeStats: {
    voice: { done: 0, total: 0, exists: false },
    image: { done: 0, total: 0, exists: false },
    video: { done: 0, total: 0, exists: false },
  },
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
  if (state.mode === 'video') {
    return {
      myths: '/api/videos/myths',
      scenes:  (name) => `/api/videos/${encodeURIComponent(name)}/scenes`,
      select:  (name) => `/api/videos/${encodeURIComponent(name)}/select`,
      regen:   (name) => `/api/videos/${encodeURIComponent(name)}/regen`,
      regenAll:(name) => `/api/videos/${encodeURIComponent(name)}/regenerate-all`,
      runnerStatus: (name) => `/api/videos/${encodeURIComponent(name)}/runner-status`,
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
  if (state.mode === 'image') return 'Ревью изображений';
  if (state.mode === 'video') return 'Ревью видео';
  return 'Ревью озвучки';
}

function cacheKey(scenario) {
  return `${state.mode}::${scenario}`;
}

// ── Init ──────────────────────────────────────────────────────────────────

async function init() {
  setupBrandAndCrumbs();
  setupModeRail();
  setupHubBindings();
  // По hash'у восстанавливаем, где был пользователь: chooser / hub / review.
  // Без этого любой F5 выкидывал на стартовый экран, что бесит при долгой
  // сверке вариантов.
  const ok = await applyHash();
  if (!ok) {
    setView('chooser');
    loadChooserMeta().catch(err => console.warn('chooser meta load failed', err));
  }
  // Браузерная навигация: popstate срабатывает на Back/Forward, hashchange —
  // на ручное редактирование hash в адресной строке. Программные push/replace
  // ни тот, ни другой не триггерят, поэтому двойного рендера не будет.
  window.addEventListener('popstate', (e) => {
    _currentDepth = (e.state && typeof e.state.depth === 'number') ? e.state.depth : 0;
    applyHash().catch(() => {});
  });
  window.addEventListener('hashchange', () => applyHash().catch(() => {}));
}

// ── URL-hash роутинг ──────────────────────────────────────────────────────
//
// Форматы:
//   #chooser                        (или пустой)
//   #hub/voice
//   #hub/image
//   #review/voice/<scenario>
//   #review/voice/<scenario>/<scene_base>
//
// Имя сценария и base сцены URL-encoded (кириллица → %D0%...).
//
// Стек history: forward-переходы (chooser→hub, hub→review) делают pushState —
// это даёт браузерному Back возможность шагать по экранам приложения, а не
// сразу выходить из вкладки. In-place уточнения (смена сцены, переключение
// режима внутри ревью) делают replaceState — чтобы не захламлять историю.
// Глубину стека держим в history.state.depth: после Back popstate отдаёт
// state предыдущей записи, и мы знаем, есть ли куда возвращаться внутри
// приложения (для in-app кнопок «назад»).

let _suppressHashWrite = false;  // во время applyHash не хотим рекурсии
let _currentDepth = 0;           // depth текущей history-записи (sync с state.depth)

function _setEntryUrl(parts, push) {
  if (_suppressHashWrite) return;
  const hash = '#' + parts.map(encodeURIComponent).join('/');
  if (!push && location.hash === hash) return;
  if (push) {
    _currentDepth += 1;
    history.pushState({ depth: _currentDepth }, '', hash);
  } else {
    history.replaceState({ depth: _currentDepth }, '', hash);
  }
}

function writeHash(parts) {
  // Refinement: меняем URL текущей записи (сцена, mode-rail внутри ревью).
  _setEntryUrl(parts, false);
}

function pushHash(parts) {
  // Forward navigation: новая запись в стеке (chooser→hub, hub→review).
  _setEntryUrl(parts, true);
}

function goBack(fallbackParts) {
  // In-app кнопки «назад». Если в стеке есть наша запись — обычный
  // history.back() (popstate сам отрисует нужный экран). Если стек пуст
  // (например, юзер F5'нул прямо в review-URL) — pushState fallback,
  // чтобы не вылететь из приложения.
  const st = history.state;
  if (st && typeof st.depth === 'number' && st.depth > 0) {
    history.back();
  } else if (fallbackParts) {
    pushHash(fallbackParts);
    applyHash().catch(() => {});
  }
}

function parseHash() {
  const raw = location.hash.replace(/^#/, '');
  if (!raw) return null;
  const parts = raw.split('/').map(decodeURIComponent);
  const view = parts[0];
  if (view === 'chooser') return { view: 'chooser' };
  if (view === 'hub') return { view: 'hub', mode: parts[1] || 'voice' };
  if (view === 'review') {
    return {
      view: 'review',
      mode: parts[1] || 'voice',
      scenario: parts[2] || null,
      sceneBase: parts[3] || null,
    };
  }
  return null;
}

async function applyHash() {
  const route = parseHash();
  if (!route) return false;

  _suppressHashWrite = true;
  try {
    if (route.view === 'chooser') {
      setView('chooser');
      loadChooserMeta().catch(() => {});
      return true;
    }
    if (route.view === 'hub') {
      setMode(['image', 'video'].includes(route.mode) ? route.mode : 'voice');
      setView('hub');
      await loadHub();
      return true;
    }
    if (route.view === 'review' && route.scenario) {
      setMode(['image', 'video'].includes(route.mode) ? route.mode : 'voice');
      await loadScenario(route.scenario, route.sceneBase);
      setView('review');
      return true;
    }
  } catch (e) {
    console.warn('applyHash failed:', e);
    return false;
  } finally {
    _suppressHashWrite = false;
  }
  return false;
}

function setView(view) {
  document.body.dataset.view = view;
  if (view === 'hub' || view === 'chooser') {
    stopAudio();
    if (typeof stopAllVideo === 'function') stopAllVideo();
    stopCosyProgress();
  }
  // Пишем минимальный hash для chooser/hub; review пишет свой в loadScenario
  if (view === 'chooser') writeHash(['chooser']);
  else if (view === 'hub') writeHash(['hub', state.mode || 'voice']);
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
  // Клик по бренду → chooser. Если в стеке есть in-app записи (hub, review),
  // отматываем сразу до корня — это совпадает с тем, как ведёт себя
  // длинный Back. Иначе делаем pushState на chooser.
  $('brand-link').addEventListener('click', (e) => {
    e.preventDefault();
    if (_currentDepth > 0) {
      history.go(-_currentDepth);
    } else {
      goToChooser();
    }
  });

  // Клик по "Ревью озвучки/изображений" → хаб текущего режима. По смыслу
  // это именно «назад к списку мифов», поэтому используем goBack:
  // если стек позволяет — нативный history.back(), иначе pushState на hub.
  $('crumb-hub').addEventListener('click', (e) => {
    e.preventDefault();
    goBack(['hub', state.mode || 'voice']);
  });
}

function goToChooser() {
  setView('chooser');
  loadChooserMeta().catch(() => {});
}

// Подтягиваем статистику для трёх плиток чузера
async function loadChooserMeta() {
  const [voiceSum, imageSum, videoSum] = await Promise.allSettled([
    fetchJSON('/api/scenarios-summary'),
    fetchJSON('/api/images/myths'),
    fetchJSON('/api/videos/myths'),
  ]);
  fillChooserMeta('chooser-voice-meta', voiceSum);
  fillChooserMeta('chooser-image-meta', imageSum);
  fillChooserMeta('chooser-video-meta', videoSum);
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
  // Forward-переход: pushState, чтобы браузерный Back возвращал на chooser,
  // а не выкидывал из приложения. setView ниже сделает replaceState на тот
  // же hash — это no-op, история не дублируется.
  pushHash(['hub', mode]);
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

  // Кнопка «+ новый миф»: создаёт папку content/<имя>/ со всей структурой
  // (prompts/, voiceover/audio, voiceover/texts, images/, video/, music/,
  // final/) и три заготовки промптов через /api/scenarios/create.
  const addBtn = $('hub-add-btn');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      onCreateNewMyth().catch(err => toast('Не удалось создать миф: ' + err.message, 'error'));
    });
  }
}

// ── Создание нового мифа ─────────────────────────────────────────────────
//
// Модалка спрашивает имя сценария → POST /api/scenarios/create → бэкенд
// раскатывает всю структуру папок (prompts, voiceover, images, video,
// music, final) и три шаблона промптов с правилами канала. После
// успеха — перезагрузка хаба и автоселект нового мифа.

async function onCreateNewMyth() {
  const name = await promptForMythName();
  if (!name) return;

  const res = await fetch('/api/scenarios/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  const data = await res.json().catch(() => ({}));

  if (!res.ok || !data.ok) {
    toast(data.error || `HTTP ${res.status}`, 'error');
    return;
  }

  toast(`Миф «${data.name}» создан · ${data.created_paths.length} путей`, 'success');

  // Перезагружаем список и подсвечиваем новый миф.
  await loadHub();
  if (state.summaries?.some(s => s.name === data.name)) {
    state.hubSelectedName = data.name;
    renderHubList();
    renderHubDetail();
  }
}

function promptForMythName() {
  const modal = $('modal');
  const titleEl = $('modal-title');
  const bodyEl = $('modal-body');
  const confirmBtn = $('modal-confirm');
  const cancelBtn = $('modal-cancel');

  titleEl.textContent = 'Новый миф';
  bodyEl.innerHTML = `
    <p style="margin:0 0 12px;color:var(--text-dim);font-size:0.85rem;line-height:1.55">
      Имя папки сценария на русском, с заглавных букв, слова через пробел —
      точно как название мифа. Будут созданы папки
      <b>prompts/</b>, <b>voiceover/</b>, <b>images/</b>, <b>video/</b>,
      <b>music/</b>, <b>final/</b> и шаблоны
      <b>voiceover.md</b>, <b>images.md</b>, <b>video.md</b>.
    </p>
    <input id="myth-name-input" type="text"
           class="modal-text-input"
           autocomplete="off"
           placeholder="например: Прометей и огонь"/>
    <p class="modal-hint">
      В шаблоне <b>voiceover.md</b> сразу зашит «кликбейтный хук» после интро —
      обязательное правило канала, удерживает зрителя в первые 3 секунды (как в Мидасе).
    </p>
  `;
  confirmBtn.textContent = 'Создать';
  cancelBtn.textContent = 'Отмена';
  confirmBtn.className = 'modal-btn modal-btn-primary';

  return new Promise(resolve => {
    const input = $('myth-name-input');
    const close = (value) => {
      modal.classList.remove('show');
      confirmBtn.onclick = null;
      cancelBtn.onclick = null;
      modal.onclick = null;
      if (input) input.onkeydown = null;
      document.removeEventListener('keydown', onKey);
      resolve(value);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); close(null); }
    };
    const submit = () => {
      const v = ((input && input.value) || '').trim();
      close(v || null);
    };
    confirmBtn.onclick = submit;
    cancelBtn.onclick = () => close(null);
    modal.onclick = (e) => { if (e.target === modal) close(null); };
    if (input) {
      input.onkeydown = (e) => {
        if (e.key === 'Enter') { e.preventDefault(); submit(); }
      };
    }
    document.addEventListener('keydown', onKey);
    modal.classList.add('show');
    requestAnimationFrame(() => input && input.focus());
  });
}

// ── Activity Rail ─────────────────────────────────────────────────────────
//
// Узкий вертикальный rail слева в review-режиме, через который можно
// одним кликом переключиться между озвучкой / картинками / видео внутри
// ОДНОГО сценария — без возврата в chooser/hub. Активная сцена
// сохраняется через base-имя (loadScenario сам откатывается на первую
// сцену, если базы нет в новом режиме).
//
// Кросс-модовая статистика подгружается при входе в review одним залпом:
// /api/scenarios-summary + /api/images/myths + /api/videos/myths.

function setupModeRail() {
  const rail = $('mode-rail');
  if (!rail) return;

  rail.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.targetMode;
      onModeRailClick(target).catch(err => {
        console.error('mode switch failed', err);
        toast('Не удалось переключить режим: ' + err.message, 'error');
      });
    });
  });

  const back = $('rail-back-btn');
  if (back) {
    back.addEventListener('click', (e) => {
      e.preventDefault();
      // Шаг назад из ревью в хаб. goBack использует history.back(),
      // если в стеке есть наша запись — тогда popstate сам перерисует.
      goBack(['hub', state.mode || 'voice']);
    });
  }
}

async function loadModeStats(scenarioName) {
  // Параллельно тянем три /myths-эндпоинта. Используем allSettled —
  // если video-эндпоинт упал, voice/image всё равно отрисуются.
  if (!scenarioName) return;
  const [voiceSum, imageSum, videoSum] = await Promise.allSettled([
    fetchJSON('/api/scenarios-summary'),
    fetchJSON('/api/images/myths'),
    fetchJSON('/api/videos/myths'),
  ]);

  function pickFor(settled) {
    if (settled.status !== 'fulfilled') {
      return { done: 0, total: 0, exists: false, error: true };
    }
    const entry = (settled.value || []).find(m => m.name === scenarioName);
    if (!entry) return { done: 0, total: 0, exists: false };
    return {
      done: entry.done || 0,
      total: entry.scene_count || 0,
      exists: true,
    };
  }

  state.modeStats = {
    voice: pickFor(voiceSum),
    image: pickFor(imageSum),
    video: pickFor(videoSum),
  };
}

function renderModeRail() {
  const rail = $('mode-rail');
  if (!rail) return;

  // SVG-кольцо: r=19 → длина окружности 2πr ≈ 119.38. Полное заполнение
  // = stroke-dashoffset 0; пустое = весь периметр (119.4). Анимация
  // транслируется CSS-transition'ом на .fill.
  const C = 119.4;

  rail.querySelectorAll('.mode-btn').forEach(btn => {
    const mode = btn.dataset.targetMode;
    const stats = state.modeStats[mode] || { done: 0, total: 0, exists: false };
    const isActive = mode === state.mode;

    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-current', isActive ? 'page' : 'false');

    // Прогресс-кольцо: пустое для несуществующего/нулевого режима
    const ring = btn.querySelector('.mode-btn-ring .fill');
    if (ring) {
      const pct = stats.total > 0 ? stats.done / stats.total : 0;
      ring.setAttribute('stroke-dashoffset', String(C * (1 - pct)));
    }

    // Точка-«нов»: показывается когда режим есть, но done=0 (новый/пустой)
    // или когда данных нет вовсе. Скрыта для активного и для готовых
    // режимов — лишний шум.
    const newDot = btn.querySelector('.mode-btn-new-dot');
    if (newDot) {
      const isNew = !isActive && (
        !stats.exists ||
        (stats.total > 0 && stats.done === 0) ||
        stats.total === 0
      );
      newDot.hidden = !isNew;
    }

    // Tooltip: счётчик + контекст про сохранение сцены
    const meta = btn.querySelector('.mode-btn-tip-meta');
    const hint = btn.querySelector('.mode-btn-tip-hint');
    if (meta) {
      if (stats.error) {
        meta.innerHTML = '<b>нет связи</b>';
      } else if (!stats.exists) {
        meta.innerHTML = '<b>нет данных</b>';
      } else if (stats.total === 0) {
        meta.innerHTML = '<b>0/0</b> · пусто';
      } else {
        const tail = isActive ? '· вы здесь' : 'проверено';
        meta.innerHTML = `<b>${stats.done}/${stats.total}</b> ${tail}`;
      }
    }
    if (hint) {
      if (isActive) {
        hint.textContent = '';
      } else if (state.activeSceneBase) {
        hint.innerHTML = `сцена <mark>${escapeHtml(state.activeSceneBase)}</mark> сохраняется`;
      } else {
        hint.textContent = '';
      }
    }
  });
}

async function onModeRailClick(targetMode) {
  if (!targetMode || targetMode === state.mode) return;

  // В hub/chooser клик по rail не должен происходить (rail скрыт через CSS),
  // но на всякий случай обрабатываем как переход в hub нового режима.
  if (!state.scenario) {
    setMode(targetMode);
    pushHash(['hub', targetMode]);
    setView('hub');
    return loadHub();
  }

  // Останавливаем плеер старого режима, чтобы не остался висеть в фоне.
  stopAudio();
  if (typeof stopAllVideo === 'function') stopAllVideo();

  // Сохраняем активную сцену через base-имя. loadScenario сам подберёт
  // совпадение или откатится на первую сцену, если базы нет в новом
  // режиме (это нормально — у видео может быть не такая же раскадровка).
  const preservedBase = state.activeSceneBase;
  setMode(targetMode);

  await loadScenario(state.scenario, preservedBase);
  renderModeRail();
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

  // Помечаем контейнеры как «свежие» — это включает CSS-анимации входа
  // ОДИН раз, на первом рендере. Без этого гейта анимации перезапускались
  // на каждый клик по сценарию и создавали видимое «дерганье».
  markHubFresh();
  renderHubList();
  renderHubDetail();
}

// data-fresh="1" → CSS включает анимации hubSlide / hubRise.
// После первого кадра атрибут снимаем, и последующие renderHubList /
// renderHubDetail отрисовываются без анимаций.
function markHubFresh() {
  const list = $('hub-list-items');
  const detail = $('hub-detail');
  if (list) list.setAttribute('data-fresh', '1');
  if (detail) detail.setAttribute('data-fresh', '1');
  // Двойной rAF: первый кадр запускает анимации, второй гарантированно
  // их не отменит (атрибут уже не нужен).
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (list) list.removeAttribute('data-fresh');
    if (detail) detail.removeAttribute('data-fresh');
  }));
}

function filterSummaries() {
  return state.summaries.filter(s => {
    if (state.hubFilter === 'published') {
      if (!s.published) return false;
    } else if (state.hubFilter === 'all') {
      // показываем всё, включая опубликованные
    } else {
      // status-фильтры (в работе / готовы / новые) — это «активная воронка
      // работы». Опубликованный миф = терминальное состояние, исключаем его
      // из этих вкладок, чтобы он не «висел» в работе после публикации.
      if (s.published) return false;
      if (s.status !== state.hubFilter) return false;
    }
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
  const { status, scene_count, done, published, published_at } = summary;
  if (published) {
    const dateStr = formatPublishedDate(published_at);
    return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · опубликован${dateStr ? ' ' + dateStr : ''}`;
  }
  if (status === 'wip') return 'материалы готовятся';
  if (status === 'new') return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · не начат`;
  if (status === 'ready') return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · готов к сборке`;
  return `${scene_count} сцен · ${done} проверено`;
}

function formatPublishedDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const months = ['янв','фев','мар','апр','мая','июн','июл','авг','сен','окт','ноя','дек'];
  return `${d.getDate()} ${months[d.getMonth()]}`;
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
    const pubCls = s.published ? 'is-published' : '';
    const pct = s.scene_count ? (s.done / s.scene_count) * 100 : 0;

    // Опубликованный миф всегда показываем как «опуб.» (даже если статус
    // ready/in_progress) — это перекрывающий маркер и в UI, и в фильтре.
    let rightCol;
    if (s.published) {
      rightCol = `<div class="hub-item-status published">опуб.</div>`;
    } else if (s.status === 'in_progress') {
      rightCol = `<div class="hub-item-bar"><div class="hub-item-bar-fill" style="width:${pct}%"></div></div>`;
    } else {
      rightCol = `<div class="hub-item-status ${s.status}">${statusLabel(s.status)}</div>`;
    }

    return `
      <div class="hub-item status-${s.status} ${pubCls} ${active}" data-name="${escapeAttr(s.name)}">
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
      const newName = el.dataset.name;
      if (newName === state.hubSelectedName) return;
      state.hubSelectedName = newName;
      // Не перестраиваем весь список (это запускает hubSlide на каждом
      // элементе и создаёт «дерганье»). Достаточно перекинуть .active.
      container.querySelectorAll('.hub-item').forEach(it => {
        it.classList.toggle('active', it.dataset.name === newName);
      });
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
        ? (cachedHubTilesHtml(summary.name)
           || `<div class="hub-list-loading" style="grid-column:1/-1">загрузка карты сцен…</div>`)
        : `<div class="hub-list-empty" style="grid-column:1/-1">сцен нет</div>`}
    </div>

    <div class="hub-dp-cta">
      <div class="hub-dp-cta-text">${ctaText}</div>
      <button class="hub-btn hub-btn-publish ${summary.published ? 'is-on' : ''}" id="hub-publish-btn" title="Пометить миф опубликованным (только визуально, ничего не блокируется)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12l5 5L20 7"/></svg>
        ${summary.published ? 'опубликован' : 'опубликован?'}
      </button>
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

  const pubBtn = $('hub-publish-btn');
  if (pubBtn) {
    pubBtn.addEventListener('click', () => togglePublishedFromHub(summary.name));
  }

  if (summary.scene_count > 0) {
    renderHubSceneTiles(summary.name);
  }
}

// ── Публикация: переключение «опубликован» ─────────────────────────────────
//
// Запрос на бэкенд + локальное обновление summary, чтобы UI мгновенно
// перерисовался без полной перезагрузки списка. Сервер хранит общий флаг
// per-scenario (один на все режимы — voice / image / video).

async function togglePublished(scenario, on) {
  const res = await fetch(`/api/scenarios/${encodeURIComponent(scenario)}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on }),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function togglePublishedFromHub(scenario) {
  const summary = state.summaries.find(s => s.name === scenario);
  if (!summary) return;
  const next = !summary.published;
  try {
    const result = await togglePublished(scenario, next);
    summary.published = !!result.published;
    summary.published_at = result.published_at;
    // Если этот же миф открыт в ревью — синхронизируем bottombar
    if (state.scenario === scenario) {
      state.scenarioPublished = summary.published;
      state.scenarioPublishedAt = summary.published_at;
      refreshBottombarPublishBtn();
    }
    renderHubList();
    renderHubDetail();
    toast(
      next ? `«${summary.display_name}» — опубликован` : `«${summary.display_name}» — отметка снята`
    );
  } catch (e) {
    toast('Не удалось переключить публикацию: ' + e.message, 'error');
  }
}

async function loadPublishedState(scenario) {
  // Пытаемся взять из summaries — это уже синхронизировано с бэкендом.
  const summary = state.summaries.find(s => s.name === scenario);
  if (summary && typeof summary.published === 'boolean') {
    state.scenarioPublished = summary.published;
    state.scenarioPublishedAt = summary.published_at || null;
    return;
  }
  // Прямой запрос — например, если в review зашли по URL и summaries
  // ещё не загружены.
  try {
    const data = await fetchJSON(`/api/scenarios/${encodeURIComponent(scenario)}/publish`);
    state.scenarioPublished = !!data.published;
    state.scenarioPublishedAt = data.published_at || null;
  } catch {
    state.scenarioPublished = false;
    state.scenarioPublishedAt = null;
  }
}

function refreshBottombarPublishBtn() {
  const btn = $('publish-btn');
  if (!btn) return;
  const label = $('publish-label');
  if (state.scenarioPublished) {
    btn.classList.add('is-on');
    if (label) {
      const dateStr = formatPublishedDate(state.scenarioPublishedAt);
      label.textContent = dateStr ? `опубликован · ${dateStr}` : 'опубликован';
    }
  } else {
    btn.classList.remove('is-on');
    if (label) label.textContent = 'опубликован?';
  }
}

async function togglePublishedFromBottombar() {
  if (!state.scenario) return;
  const next = !state.scenarioPublished;
  try {
    const result = await togglePublished(state.scenario, next);
    state.scenarioPublished = !!result.published;
    state.scenarioPublishedAt = result.published_at || null;
    refreshBottombarPublishBtn();
    // Синхронизируем summary, чтобы хаб тоже был актуален при возврате
    const summary = state.summaries.find(s => s.name === state.scenario);
    if (summary) {
      summary.published = state.scenarioPublished;
      summary.published_at = state.scenarioPublishedAt;
    }
    toast(next ? 'миф помечен опубликованным' : 'отметка снята');
  } catch (e) {
    toast('Не удалось переключить публикацию: ' + e.message, 'error');
  }
}

// Возвращает готовый HTML плиток если сцены уже в кэше — иначе null.
// Используется в renderHubDetail, чтобы избежать промежуточного состояния
// «загрузка карты сцен…» на каждом клике по уже посещённому сценарию.
function cachedHubTilesHtml(scenario) {
  const ckey = cacheKey(scenario);
  const scenes = state.hubSceneCache[ckey];
  if (!scenes) return null;
  return scenesTilesHtml(scenes);
}

function scenesTilesHtml(scenes) {
  return scenes.map(sc => {
    const cls = sc.status === 'done' ? 'done' : sc.status === 'regen' ? 'regen' : '';
    const num = sc.base.replace(/^[a-zA-Zа-яА-Я]+_0*/, '') || sc.base;
    return `<div class="hub-scene-tile ${cls}" data-base="${escapeAttr(sc.base)}" title="${escapeAttr(sc.base)}${sc.text ? ': ' + escapeAttr(sc.text.slice(0, 60)) : ''}">${escapeHtml(num)}</div>`;
  }).join('');
}

async function renderHubSceneTiles(scenario) {
  const tilesContainer = $('hub-scene-tiles');
  if (!tilesContainer) return;

  const ckey = cacheKey(scenario);
  let scenes = state.hubSceneCache[ckey];
  const wasCached = !!scenes;
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

  // Если плитки уже отрисованы синхронно из кэша (renderHubDetail вставил
  // готовый HTML), то innerHTML повторно не трогаем — просто навешиваем
  // обработчики кликов. Это полностью исключает повторный layout/paint.
  const alreadyRendered = wasCached
    && tilesContainer.children.length === scenes.length
    && tilesContainer.firstElementChild
    && tilesContainer.firstElementChild.classList.contains('hub-scene-tile');

  if (!alreadyRendered) {
    tilesContainer.innerHTML = scenesTilesHtml(scenes);
  }

  tilesContainer.querySelectorAll('.hub-scene-tile').forEach((tile, idx) => {
    tile.addEventListener('click', () => {
      openScenarioReview(scenario, scenes[idx].base);
    });
  });
}

async function openScenarioReview(scenario, targetSceneBase = null) {
  // Forward-переход hub→review: pushState новой записи. Внутри loadScenario
  // дальше будет replaceState с тем же URL (только base сцены добавится) —
  // это уточнение текущей записи, без второго push. Делаем push до await,
  // чтобы быстрый Back во время загрузки тоже работал предсказуемо.
  const parts = ['review', state.mode, scenario];
  if (targetSceneBase) parts.push(targetSceneBase);
  pushHash(parts);
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
  // Сразу пишем hash — даже если fetchJSON упадёт, пользователь увидит URL
  // и сможет поделиться/перезагрузить и попасть куда нужно.
  writeHash(['review', state.mode, scenario, ...(targetSceneBase ? [targetSceneBase] : [])]);

  // Подтягиваем флаг публикации для bottombar-кнопки. Не блокируем
  // основную загрузку — даже если упадёт, ревью откроется.
  loadPublishedState(scenario)
    .then(() => refreshBottombarPublishBtn())
    .catch(err => console.warn('publish-state failed', err));

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

  // Помечаем сайдбар как «свежий» — slideIn-анимация на пунктах меню
  // должна сработать только на первом рендере при заходе в сценарий.
  // Последующие renderSidebar() (на каждый выбор варианта / toggle
  // регенерации) идут без анимации, иначе все 30 пунктов «дёргаются».
  const navList = $('scene-nav-list');
  if (navList) {
    navList.setAttribute('data-fresh', '1');
    requestAnimationFrame(() => requestAnimationFrame(() => {
      navList.removeAttribute('data-fresh');
    }));
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

  // Кросс-модовая статистика для rail. Не блокируем основную загрузку:
  // данные про другие режимы — приятный бонус, а не критика. Если упадёт —
  // rail просто покажет «нет связи» в tooltip.
  loadModeStats(scenario)
    .then(() => renderModeRail())
    .catch(err => console.warn('loadModeStats failed', err));
  // Сразу рисуем rail в текущем виде — активный режим подсветится из
  // state.mode даже без статистики, на пустых счётчиках.
  renderModeRail();
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
  renderSidebarAction();

  const isVoice = state.mode === 'voice';
  // batch-active маркируем только если сейчас открыт тот же сценарий,
  // на котором крутится батч — иначе в чужом мифе подсветится сцена
  // с совпадающим base-именем.
  const batchActiveBase = state.cosyBatch
      && state.cosyBatch.active
      && state.cosyBatch.scenario === state.scenario
    ? state.cosyBatch.currentBase
    : null;

  sceneNavList.innerHTML = state.scenes.map(scene => {
    const approvedClass = scene.approved ? 'approved' : '';
    const statusClass = scene.status === 'done' ? 'done'
                      : scene.status === 'regen' ? 'regen' : '';
    const active = scene.base === state.activeSceneBase ? 'active' : '';
    const batchActive = scene.base === batchActiveBase ? 'batch-active' : '';
    const preview = scene.text || '(нет текста)';
    const badge = scene.approved
      ? `<div class="nav-approved-badge" title="Одобрено — ${escapeHtml(scene.approved)}">★</div>`
      : '';

    // В voice-режиме заменяем текстовый бейдж N/10 на 10-пип индикатор.
    // Пипсы показывают: сколько вариантов уже есть (зелёный), какой
    // генерируется сейчас (оранжевый пульс), и сколько осталось (серые).
    // В image-режиме пипсы прячутся через CSS.
    let pipsHtml = '';
    let cosyBadge = '';
    if (isVoice) {
      const requested = BATCH_META.variants;
      // Источник «сколько уже готово»: приоритет — live-значение из batch,
      // иначе scene.cosy.produced (если есть недавняя активность),
      // иначе — число файлов в scene.variants.
      let produced = (scene.variants || []).length;
      let isActive = false;
      if (scene.base === batchActiveBase) {
        produced = state.cosyBatch.produced;
        isActive = true;
      } else if (scene.cosy && !scene.cosy.done) {
        produced = scene.cosy.produced || 0;
      }
      const pips = Array.from({ length: requested }, (_, i) => {
        let cls = '';
        if (i < produced) cls = 'done';
        else if (isActive && i === produced) cls = 'active';
        return `<div class="nav-pip ${cls}"></div>`;
      }).join('');
      pipsHtml = `<div class="nav-pips" title="${produced}/${requested} вариантов">${pips}</div>`;

      // Оставляем текстовый badge только для упавшей генерации —
      // пипсы этот случай не отличают от «ещё не генерировалось».
      if (scene.cosy && scene.cosy.failed) {
        cosyBadge = `<div class="nav-cosy-badge failed" title="CosyVoice упал — открой сцену, чтобы увидеть лог">!</div>`;
      }
    } else {
      // Image-режим: 4-пип индикатор по числу вариантов (Flow обычно даёт 4).
      // CSS грид у .nav-pips переключается на repeat(4) через data-mode,
      // но список всё равно рендерим из IMAGE_BATCH_META.variants = 4.
      const requested = IMAGE_BATCH_META.variants;
      const produced = Math.min((scene.variants || []).length, requested);
      const pips = Array.from({ length: requested }, (_, i) => {
        const cls = i < produced ? 'done' : '';
        return `<div class="nav-pip ${cls}"></div>`;
      }).join('');
      pipsHtml = `<div class="nav-pips" title="${produced}/${requested} картинок">${pips}</div>`;
    }

    return `
      <div class="scene-nav-item ${approvedClass} ${statusClass} ${active} ${batchActive}" data-base="${scene.base}">
        <div class="nav-indicator"></div>
        <div class="nav-num">${scene.base.replace('scene_', '')}</div>
        <div class="nav-text" title="${escapeHtml(preview)}">${escapeHtml(preview)}</div>
        ${pipsHtml}
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
  const baseChanged = state.activeSceneBase !== base;
  state.activeSceneBase = base;
  // Обновляем hash, чтобы при F5 открылась та же сцена
  if (state.scenario) {
    writeHash(['review', state.mode, state.scenario, base]);
  }
  stopAudio();
  sceneNavList.querySelectorAll('.scene-nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.base === base);
  });

  const scene = state.scenes.find(s => s.base === base);
  if (!scene) return;

  emptyState.style.display = 'none';
  sceneDetail.style.display = '';

  // Анимация fadeUp на variant-card должна сработать только когда сцена
  // действительно сменилась, а не на повторных перерендерах той же сцены
  // (например, при обновлении прогресса CosyVoice). Гейт через data-fresh.
  if (baseChanged) {
    sceneDetail.setAttribute('data-fresh', '1');
    requestAnimationFrame(() => requestAnimationFrame(() => {
      sceneDetail.removeAttribute('data-fresh');
    }));
  }

  // Видео-режим — кинотеатр-layout, рендерится отдельной функцией
  if (state.mode === 'video') {
    renderVideoSceneDetail(scene);
    return;
  }

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
          <div class="text-block-header prompt-header-row">
            <span>Промпт</span>
            <button class="copy-prompt-btn" type="button" id="copy-prompt-btn" title="Скопировать весь промпт">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <span>Копировать</span>
            </button>
          </div>
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
  if (isImage && scene.prompt) {
    attachCopyPromptHandler(scene.prompt);
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
  // Cache-buster: после перегенерации mp3 имя файла не меняется, но
  // контент другой — без query-параметра браузер отдаёт старую озвучку
  // из HTTP-кеша. size_kb меняется между разными генерациями, поэтому
  // служит стабильным хешем содержимого.
  const cacheKey = variant.size_kb != null ? `?v=${variant.size_kb}` : '';
  const audioUrl = `/audio/${encodeURIComponent(state.scenario)}/${audioPath}${cacheKey}`;
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
        <button class="v-image-zoom" title="Посмотреть крупнее" aria-label="zoom">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="7"/>
            <path d="m21 21-4.3-4.3"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
            <line x1="11" y1="8" x2="11" y2="14"/>
          </svg>
        </button>
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
  const zoomBtn = card.querySelector('.v-image-zoom');
  const selectBtn = card.querySelector('.v-select-btn');

  // Клик по самой картинке — выбрать вариант. Отдельная кнопка с лупой
  // в углу открывает лайтбокс, чтобы не мешать основному жесту.
  if (img) {
    img.addEventListener('click', (e) => {
      e.stopPropagation();
      onSelectVariant(card.dataset.base, card.dataset.variant);
    });
  }

  if (zoomBtn) {
    zoomBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (img) openLightbox(img.src, card.dataset.base, card.dataset.variant);
    });
  }

  selectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    onSelectVariant(card.dataset.base, card.dataset.variant);
  });
}

// ─────────────────────────────────────────────────────────────────────────
// VIDEO REVIEW — режим «видео» (cinema layout)
// ─────────────────────────────────────────────────────────────────────────
//
// Главный плеер 9:16 в центре, ряд дублей под ним, info-панель справа
// (текст · опорный кадр · промпт · звуки). Дубли — это все варианты
// scene_NN_vN.mp4, что нашёл backend в content/<миф>/video/. Активный
// дубль (selected или первый) воспроизводится в большом плеере; клик по
// карточке другого дубля переключает источник.

function extractApprovedBasename(path) {
  // Из «content/Тесей и Минотавр/images/approved_images/scene_15_v1.jpg»
  // получаем «scene_15_v1.jpg» — для /video-thumb/<scenario>/<filename>.
  if (!path) return '';
  return path.split(/[\\/]/).filter(Boolean).pop() || '';
}

function videoUrl(filename) {
  // Cache-buster по имени — после регенерации Veo может перезаписать
  // scene_NN_v1.mp4 новым файлом, query-параметр обходит HTTP-кеш.
  const sc = encodeURIComponent(state.scenario);
  return `/video/${sc}/${encodeURIComponent(filename)}?t=${Date.now()}`;
}

function videoThumbUrl(approvedPath) {
  const fname = extractApprovedBasename(approvedPath);
  if (!fname) return '';
  return `/video-thumb/${encodeURIComponent(state.scenario)}/${encodeURIComponent(fname)}`;
}

function formatSoundsList(sounds) {
  // Парсим строку «звук1 (eng1), звук2 (eng2)» в список <div class="vid-sound">
  if (!sounds) return '';
  const items = sounds.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
  return items.map(item => {
    const m = item.match(/^(.+?)\s*\(([^)]+)\)\s*\.?$/);
    if (m) {
      return `<div class="vid-sound">${escapeHtml(m[1].trim())}<em>${escapeHtml(m[2].trim())}</em></div>`;
    }
    return `<div class="vid-sound">${escapeHtml(item)}</div>`;
  }).join('');
}

function pickActiveVariant(scene) {
  const variants = scene.variants || [];
  if (!variants.length) return null;
  if (scene.selected) {
    const v = variants.find(v => v.variant === scene.selected);
    if (v) return v;
  }
  return variants[0];
}

function renderVideoSceneDetail(scene) {
  const idx = state.scenes.findIndex(s => s.base === scene.base);
  const total = state.scenes.length;
  const prevDisabled = idx <= 0 ? 'disabled' : '';
  const nextDisabled = idx >= total - 1 ? 'disabled' : '';

  const variants = scene.variants || [];
  const active = pickActiveVariant(scene);
  const refThumb = videoThumbUrl(scene.image);
  const refName = extractApprovedBasename(scene.image);

  const sceneNum = parseInt(scene.base.replace('scene_', ''), 10) || (idx + 1);

  // Главный плеер: <video> с активным дублем, либо placeholder с опорным кадром
  const playerInner = active
    ? `
      <video class="vid-player-video" id="vid-main-player"
             src="${videoUrl(active.filename)}"
             ${refThumb ? `poster="${refThumb}"` : ''}
             preload="metadata"
             playsinline></video>
      <div class="vid-take-badge">Дубль ${active.variant.replace('v','').padStart(2,'0')} / ${variants.length}</div>
      <div class="vid-tc-overlay" id="vid-tc-overlay"><b>00:00</b> <span>/ —</span></div>
      <button class="vid-play-btn" id="vid-play-btn" aria-label="play">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      </button>
    `
    : `
      <div class="vid-player-empty">
        ${refThumb ? `<img class="vid-player-empty-thumb" src="${refThumb}" alt="reference"/>` : ''}
        <div class="vid-player-empty-overlay">
          <div class="vid-player-empty-eyebrow">опорный кадр</div>
          <div class="vid-player-empty-msg">Veo ещё не сгенерировал клип<br>для этой сцены</div>
          <div class="vid-player-empty-hint">Нажми «Сгенерировать видео» в сайдбаре</div>
        </div>
      </div>
    `;

  // Ряд дублей под плеером
  const takesHTML = variants.length
    ? variants.map(v => renderVideoTakeCard(scene, v, refThumb, active)).join('')
    : `<div class="vid-takes-empty">— дублей пока нет —</div>`;

  // Скруббер активен только если есть дубль
  const scrubberHTML = active
    ? `
      <div class="vid-scrubber-row">
        <div class="vid-tc-big" id="vid-tc-big">00:00 <small>/ —</small></div>
        <div class="vid-scrub" id="vid-scrub">
          <div class="vid-scrub-fill" id="vid-scrub-fill"></div>
          <div class="vid-scrub-handle" id="vid-scrub-handle"></div>
        </div>
        <div class="vid-pl-controls">
          <button class="vid-pl-btn" id="vid-step-back" title="-1 секунда">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>
          </button>
          <button class="vid-pl-btn" id="vid-loop" title="зацикленно">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
              <path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 014-4h14"/>
              <path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 01-4 4H3"/>
            </svg>
          </button>
          <button class="vid-pl-btn" id="vid-step-fwd" title="+1 секунда">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>
          </button>
        </div>
      </div>
    `
    : '';

  // Info panel
  const infoBlocks = [];
  if (scene.text) {
    infoBlocks.push(`
      <div class="vid-info-block">
        <h4>Текст сцены</h4>
        <div class="vid-info-text">${escapeHtml(scene.text)}</div>
      </div>
    `);
  }
  if (refThumb) {
    infoBlocks.push(`
      <div class="vid-info-block">
        <h4>Опорный кадр <span>${escapeHtml(refName)}</span></h4>
        <img class="vid-info-thumb" src="${refThumb}" alt="reference"/>
      </div>
    `);
  }
  if (scene.prompt) {
    infoBlocks.push(`
      <div class="vid-info-block">
        <h4>Промпт <span>action / motion</span></h4>
        <button class="copy-prompt-btn copy-prompt-btn-vid" type="button" id="copy-prompt-btn" title="Скопировать весь промпт">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          <span>Копировать</span>
        </button>
        <div class="vid-info-prompt">${escapeHtml(scene.prompt)}</div>
      </div>
    `);
  }
  if (scene.sounds) {
    infoBlocks.push(`
      <div class="vid-info-block">
        <h4>Звуки</h4>
        <div class="vid-info-sounds">${formatSoundsList(scene.sounds)}</div>
      </div>
    `);
  }
  infoBlocks.push(`
    <div class="vid-info-block vid-info-actions">
      <button class="vid-regen-btn" id="regen-btn">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M3 12a9 9 0 0 1 15-6.7l3-3v8h-8l3-3a6 6 0 1 0 1.5 4.7"/>
        </svg>
        Пометить на перегенерацию
      </button>
    </div>
  `);

  sceneDetail.innerHTML = `
    <div class="vid-cinema">
      <div class="vid-cinema-main">
        <div class="vid-marquee">
          <div class="vid-marquee-num">
            <span>Сцена <em>${sceneNum}</em></span>
            <small>${escapeHtml(scene.base)} · ${idx+1} / ${total}</small>
          </div>
          <div class="vid-marquee-id">${escapeHtml(scene.base)}</div>
          <div class="vid-marquee-nav">
            <button class="vid-nav-btn" id="nav-prev" ${prevDisabled}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
              пред.
            </button>
            <button class="vid-nav-btn" id="nav-next" ${nextDisabled}>
              след.
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>

        <div class="vid-screening">
          <div class="vid-perf">${'<div></div>'.repeat(7)}</div>
          <div class="vid-screen-wrap">
            <div class="vid-player ${active ? '' : 'is-empty'}" id="vid-player">
              ${playerInner}
            </div>
          </div>
          <div class="vid-side-meta">
            <div>9 : 16 vertical</div>
            <div>Veo 3.1 · img-to-video</div>
            <div>${variants.length} ${plural(variants.length, 'дубль', 'дубля', 'дублей')}</div>
          </div>
        </div>

        <div class="vid-stage-foot">
          ${scrubberHTML}
          <div class="vid-takes-section-header">
            <h2>Дубли</h2>
            <div class="vid-takes-count">${variants.length} ${plural(variants.length, 'вариант', 'варианта', 'вариантов')}</div>
          </div>
          <div class="vid-takes-row">${takesHTML}</div>
        </div>
      </div>

      <aside class="vid-cinema-info">
        ${infoBlocks.join('')}
      </aside>
    </div>
  `;

  // ── Привязка обработчиков ──
  $('nav-prev')?.addEventListener('click', () => navigateScene(-1));
  $('nav-next')?.addEventListener('click', () => navigateScene(1));
  $('regen-btn')?.addEventListener('click', () => onRegenerate(scene.base));

  if (scene.prompt) {
    attachCopyPromptHandler(scene.prompt);
  }

  sceneDetail.querySelectorAll('.vid-take').forEach(card => attachVideoTakeHandlers(card, scene));

  if (active) {
    bindVideoMainPlayer(scene);
  }
}

function renderVideoTakeCard(scene, variant, refThumb, activeVariant) {
  const isChosen = scene.selected === variant.variant;
  const isActive = activeVariant && activeVariant.variant === variant.variant;
  const classes = ['vid-take', isChosen ? 'chosen' : '', isActive ? 'active-take' : ''].filter(Boolean).join(' ');
  const variantLabel = variant.variant.replace('v', '').padStart(2, '0');
  const btnLabel = isChosen ? '✓ Выбрано' : 'Выбрать';
  return `
    <div class="${classes}" data-base="${escapeAttr(scene.base)}" data-variant="${escapeAttr(variant.variant)}" data-filename="${escapeAttr(variant.filename)}">
      <div class="vid-take-thumb">
        <video class="vid-take-video" muted playsinline preload="metadata"
               src="${videoUrl(variant.filename)}"
               ${refThumb ? `poster="${refThumb}"` : ''}></video>
        <div class="vid-take-play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div>
      </div>
      <div class="vid-take-info">
        <div class="vid-take-title">Дубль ${variantLabel}${isChosen ? ' ✓' : ''}</div>
        <div class="vid-take-meta"><span>${variant.size_mb} МБ</span> · ${escapeHtml(variant.filename)}</div>
      </div>
      <button class="vid-take-btn">${btnLabel}</button>
    </div>
  `;
}

function attachVideoTakeHandlers(card, scene) {
  const base = card.dataset.base;
  const variant = card.dataset.variant;
  const selectBtn = card.querySelector('.vid-take-btn');
  const thumb = card.querySelector('.vid-take-thumb');

  // Клик по миниатюре — сделать активной (загрузить в большой плеер).
  // Само переключение «Выбрать» — отдельной кнопкой, чтобы случайный
  // клик не переписывал selections.json.
  thumb.addEventListener('click', () => activateVideoTake(scene, variant));
  selectBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    onSelectVariant(base, variant);
  });
}

function activateVideoTake(scene, variantId) {
  const variant = (scene.variants || []).find(v => v.variant === variantId);
  if (!variant) return;
  const player = $('vid-main-player');
  if (player) {
    player.src = videoUrl(variant.filename);
    player.load();
    player.play().catch(() => {});
  }
  // Подсветка активной take-карточки
  sceneDetail.querySelectorAll('.vid-take').forEach(c => {
    c.classList.toggle('active-take', c.dataset.variant === variantId);
  });
  // Обновляем бейдж
  const badge = sceneDetail.querySelector('.vid-take-badge');
  if (badge) {
    const total = (scene.variants || []).length;
    badge.textContent = `Дубль ${variantId.replace('v','').padStart(2,'0')} / ${total}`;
  }
}

function bindVideoMainPlayer(scene) {
  const player = $('vid-main-player');
  const playBtn = $('vid-play-btn');
  const tcOverlay = $('vid-tc-overlay');
  const tcBig = $('vid-tc-big');
  const scrub = $('vid-scrub');
  const scrubFill = $('vid-scrub-fill');
  const scrubHandle = $('vid-scrub-handle');
  const stepBack = $('vid-step-back');
  const stepFwd = $('vid-step-fwd');
  const loopBtn = $('vid-loop');
  if (!player) return;

  state.currentPlayingVideo = player;

  function setTcLabels() {
    const cur = formatTime(player.currentTime || 0);
    const dur = isFinite(player.duration) ? formatTime(player.duration) : '—';
    if (tcOverlay) tcOverlay.innerHTML = `<b>${cur}</b> <span>/ ${dur}</span>`;
    if (tcBig) tcBig.innerHTML = `${cur} <small>/ ${dur}</small>`;
  }

  function setScrub() {
    if (!isFinite(player.duration) || player.duration === 0) return;
    const pct = (player.currentTime / player.duration) * 100;
    if (scrubFill) scrubFill.style.width = pct + '%';
    if (scrubHandle) scrubHandle.style.left = pct + '%';
  }

  function togglePlayMain() {
    if (player.paused) {
      // Останавливаем любое чужое аудио — один источник звука за раз
      stopAudio();
      player.play().catch(err => console.warn('video play failed', err));
    } else {
      player.pause();
    }
  }

  player.addEventListener('loadedmetadata', setTcLabels);
  player.addEventListener('timeupdate', () => { setTcLabels(); setScrub(); });
  player.addEventListener('play', () => $('vid-player')?.classList.add('is-playing'));
  player.addEventListener('pause', () => $('vid-player')?.classList.remove('is-playing'));
  player.addEventListener('ended', () => {
    $('vid-player')?.classList.remove('is-playing');
    if (loopBtn?.classList.contains('on')) {
      player.currentTime = 0;
      player.play().catch(() => {});
    }
  });

  if (playBtn) playBtn.addEventListener('click', (e) => { e.stopPropagation(); togglePlayMain(); });
  $('vid-player')?.addEventListener('click', togglePlayMain);

  if (scrub) {
    scrub.addEventListener('click', (e) => {
      if (!isFinite(player.duration)) return;
      const rect = scrub.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      player.currentTime = ratio * player.duration;
      setScrub();
      setTcLabels();
    });
  }
  if (stepBack) stepBack.addEventListener('click', (e) => { e.stopPropagation(); player.currentTime = Math.max(0, player.currentTime - 1); });
  if (stepFwd)  stepFwd.addEventListener('click', (e) => { e.stopPropagation(); player.currentTime = Math.min(player.duration || 999, player.currentTime + 1); });
  if (loopBtn) loopBtn.addEventListener('click', (e) => { e.stopPropagation(); loopBtn.classList.toggle('on'); player.loop = loopBtn.classList.contains('on'); });
}

function stopAllVideo() {
  if (state.currentPlayingVideo) {
    try { state.currentPlayingVideo.pause(); } catch (e) { /* noop */ }
    state.currentPlayingVideo = null;
  }
  // Также все take-видео — на всякий
  document.querySelectorAll('.vid-take-video').forEach(v => {
    try { v.pause(); } catch (e) { /* noop */ }
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
  // Останавливаем «Песнь целиком», если она играет — один источник звука за раз.
  if (typeof stopFullSong === 'function') stopFullSong();
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

    if (state.mode === 'video') {
      // У видео карточки помечены классом .vid-take, не .variant-card —
      // обновляем точечно: визуальное состояние без перерисовки плеера,
      // чтобы не сбросить currentTime воспроизведения.
      sceneDetail.querySelectorAll('.vid-take').forEach(card => {
        const v = card.dataset.variant;
        const isChosen = v === newVariant;
        card.classList.toggle('chosen', isChosen);
        const btn = card.querySelector('.vid-take-btn');
        if (btn) btn.textContent = isChosen ? '✓ Выбрано' : 'Выбрать';
        const title = card.querySelector('.vid-take-title');
        if (title) {
          const num = (v || '').replace('v', '').padStart(2, '0');
          title.textContent = `Дубль ${num}${isChosen ? ' ✓' : ''}`;
        }
      });
    } else {
      updateVariantCardsUI(base, newVariant);
    }
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
  // Параметры жёстко зафиксированы пользователем: 10 вариантов, скорость 1.0,
  // prompt-wav = content/Ящик Пандоры/TTS.mp3, prompt-text = TTS.txt.
  const cosyParams = {
    model: 'Fun-CosyVoice3-0.5B',
    variants: 10,
    speed: 1.0,
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

  // Останавливаем плеер ДО запроса: на Windows HTML5 <audio> держит open handle
  // на проигрываемый mp3, и бэкенд при попытке удалить старый approved-файл
  // (sentence_NNN_vK.mp3) падает с PermissionError [WinError 32]. На бэке
  // тоже есть retry-страховка, но проще не упираться в неё.
  stopAudio();

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
      // Одобренный вариант уходит в outdated/ вместе с остальными — сам
      // approved_sentences/*.mp3 остаётся до следующего finalize, но это
      // уже устаревший файл, и в UI звёздочка / рамка вводят в заблуждение.
      scene.approved = null;
      scene.status = 'regen';
      // Счётчик вариантов тоже обнуляем — бэкенд уже переместил файлы в
      // outdated/, пипсы без этого рисуются полными (из state.scenes).
      scene.variants = [];
    }

    // Запускаем поллинг прогресса ДО re-render sidebar — чтобы блок
    // действия сразу отобразил состояние «идёт перегенерация».
    if (!isImage) {
      startCosyProgress(base, {
        requested: res.variants ?? cosyParams.variants,
        model: res.model || cosyParams.model,
        speed: res.speed ?? cosyParams.speed,
        promptWav: res.prompt_wav || cosyParams.promptWav,
      });
    }

    updateVariantCardsUI(base, null);
    // Полный re-render сайдбара: убирает .approved класс, звёздочку,
    // обнуляет пипсы и подтягивает верхний блок действия через action-slot.
    renderSidebar();
    updateStats();
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
  speed: 1.0,
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
        // Live-обновление пипсов этой строки + верхнего блока действия.
        // Без этого per-scene regen оставляет пипсы и «Готово 35/35»
        // в замороженном состоянии до полного завершения.
        updateSidebarPips(base, status.produced || 0, status.requested || BATCH_META.variants);
        renderSidebarAction();
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

// ── Batch CosyVoice orchestration ─────────────────────────────────────────
//
// Массовая генерация «одной кнопкой»: JS последовательно вызывает
// /api/regenerate-cosyvoice для каждой сцены без полного набора вариантов
// и поллит /api/cosyvoice-status до завершения. Никаких изменений в бэкенде
// не требуется — оркестрация полностью на клиенте. Минус — при перезагрузке
// страницы batch-состояние теряется (текущая сцена сама добежит до конца,
// а следующие уже не запустятся, пока пользователь снова не нажмёт кнопку).

const BATCH_META = {
  model: 'Fun-CosyVoice3-0.5B',
  variants: 10,
  speed: 1.0,
  promptWav: 'content/Ящик Пандоры/TTS.mp3',
};

// Image-батч работает иначе — один subprocess (imagefx_runner.py --auto),
// который сам обходит все сцены из prompts/images.md. Клиент только поллит
// прогресс через /api/images/<scenario>/imagefx-status.
const IMAGE_BATCH_META = {
  variants: 4,  // типичный выход Flow/Nano Banana
};

state.imageBatch = {
  active: false,
  total: 0,
  done: 0,
  pollTimer: null,
  error: null,
  logTail: '',
};

// Video-батч — один subprocess (automation/video_runner.py), один Veo-клип
// на сцену за прогон (~80 сек). Клиент поллит /api/videos/<scenario>/runner-status.
state.videoBatch = {
  active: false,
  total: 0,
  done: 0,            // сцен с хотя бы одним клипом
  clipsTotal: 0,      // суммарное число дублей
  pollTimer: null,
  error: null,
  pid: null,
};

state.cosyBatch = {
  active: false,
  queue: [],          // массив base-имён, ожидающих генерации
  currentBase: null,
  total: 0,
  completed: 0,
  produced: 0,        // сколько файлов в текущей сцене
  requested: BATCH_META.variants,
  startedAt: 0,
  pollTimer: null,
  cancelRequested: false,
  error: null,
};

function scenesNeedingVoice() {
  return state.scenes
    .filter(s => (s.variants || []).length < BATCH_META.variants)
    .map(s => s.base);
}

async function startCosyBatch() {
  if (state.cosyBatch.active) return;
  const queue = scenesNeedingVoice();
  if (!queue.length) {
    toast('У всех предложений уже по 10 вариантов', 'success');
    return;
  }

  const ok = await showModal({
    title: 'Озвучить весь миф?',
    bodyHtml: `
      Запустим CosyVoice 3 последовательно на <b>${queue.length}</b> ${plural(queue.length, 'предложение', 'предложения', 'предложений')}.
      <div class="mb-stats" style="margin-top:12px">
        <div class="mb-stat"><span class="mb-stat-label">Модель</span><span class="mb-stat-num">${BATCH_META.model}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">Вариантов на предложение</span><span class="mb-stat-num">${BATCH_META.variants}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">Скорость</span><span class="mb-stat-num">${BATCH_META.speed}</span></div>
      </div>
      <div class="mb-note" style="margin-top:10px">
        Клон из <code>${BATCH_META.promptWav}</code>.
        Оценочное время — около <b>${Math.ceil(queue.length * 45 / 60)}</b> мин.
        Во время работы можно открывать любую уже готовую сцену и ревьюить.
      </div>
    `,
    confirmText: 'Запустить',
  });
  if (!ok) return;

  state.cosyBatch = {
    active: true,
    // Фиксируем сценарий на момент старта — все запросы и поллы должны идти
    // по нему, даже если пользователь уйдёт смотреть другой проект.
    scenario: state.scenario,
    queue,
    currentBase: null,
    total: queue.length,
    completed: 0,
    produced: 0,
    requested: BATCH_META.variants,
    startedAt: Date.now(),
    pollTimer: null,
    cancelRequested: false,
    error: null,
  };
  renderSidebarAction();
  batchNext();
}

async function batchNext() {
  if (!state.cosyBatch.active) return;
  if (state.cosyBatch.cancelRequested) {
    state.cosyBatch.active = false;
    state.cosyBatch.currentBase = null;
    toast('Генерация прервана', 'success');
    renderSidebarAction();
    renderSidebar();
    return;
  }

  const next = state.cosyBatch.queue.shift();
  const batchScenario = state.cosyBatch.scenario;
  if (!next) {
    state.cosyBatch.active = false;
    state.cosyBatch.currentBase = null;
    toast(`Озвучка готова · ${state.cosyBatch.completed}/${state.cosyBatch.total}`, 'success');
    renderSidebarAction();
    // Перезагружаем только если пользователь сейчас смотрит тот же сценарий,
    // на котором крутился батч; иначе ему ничего обновлять не надо.
    if (state.scenario === batchScenario) {
      await loadScenario(state.scenario, state.activeSceneBase);
    }
    return;
  }

  state.cosyBatch.currentBase = next;
  state.cosyBatch.produced = 0;
  renderSidebarAction();
  renderSidebar();

  try {
    const res = await postJSON(api().regen(batchScenario), { base: next });
    state.cosyBatch.requested = res.variants ?? BATCH_META.variants;

    await waitForCosyScene(next, state.cosyBatch.requested);
    state.cosyBatch.completed++;
    // Подтягиваем свежие варианты для только что готовой сцены, чтобы
    // ревьюер мог открыть её и услышать озвучку, не дожидаясь конца батча.
    await refreshSceneVariants(batchScenario, next);
    renderSidebarAction();
    batchNext();
  } catch (e) {
    state.cosyBatch.active = false;
    state.cosyBatch.error = e.message || 'неизвестная ошибка';
    toast(`Ошибка на ${next}: ${state.cosyBatch.error}`, 'error');
    renderSidebarAction();
    renderSidebar();
  }
}

// Подтягиваем варианты конкретной сцены без полного reload-а сайдбара —
// чтобы во время батча можно было открыть готовую сцену и услышать варианты.
// Если пользователь ушёл смотреть другой сценарий — обновлять state.scenes
// нельзя (там сцены другого мифа), поэтому просто молча выходим.
async function refreshSceneVariants(scenario, base) {
  if (state.scenario !== scenario) return;
  try {
    const data = await fetchJSON(api().scenes(scenario));
    if (state.scenario !== scenario) return;
    const updated = data.scenes.find(s => s.base === base);
    if (!updated) return;
    const idx = state.scenes.findIndex(s => s.base === base);
    if (idx === -1) return;
    // Сохраняем cosy-индикатор сайдбара, обновляем variants + status
    const cosy = state.scenes[idx].cosy;
    state.scenes[idx] = { ...updated, cosy };
    // Если открыта именно эта сцена — перерендерим правую панель
    if (state.activeSceneBase === base) {
      activateScene(base);
    }
  } catch (e) {
    console.warn('refreshSceneVariants failed', e);
  }
}

function waitForCosyScene(base, requested) {
  // Имя сценария фиксируем в момент старта поллинга — иначе при переключении
  // проекта запросы пойдут не в ту папку и батч зависнет навсегда.
  const scenario = state.cosyBatch.scenario;
  return new Promise((resolve, reject) => {
    const poll = async () => {
      if (state.cosyBatch.cancelRequested) {
        return reject(new Error('отменено'));
      }
      try {
        const url = `/api/cosyvoice-status/${encodeURIComponent(scenario)}/${encodeURIComponent(base)}`;
        const status = await fetchJSON(url);

        state.cosyBatch.produced = status.produced || 0;
        updateSidebarPips(base, state.cosyBatch.produced, requested);
        renderSidebarAction();

        if (status.done) return resolve();
        // Runner упал, если есть error_hint и ни одного файла не родилось
        if (status.error_hint && (status.produced || 0) === 0) {
          return reject(new Error(status.error_hint));
        }
        state.cosyBatch.pollTimer = setTimeout(poll, 1500);
      } catch (e) {
        state.cosyBatch.pollTimer = setTimeout(poll, 3000);
      }
    };
    poll();
  });
}

function cancelCosyBatch() {
  state.cosyBatch.cancelRequested = true;
  if (state.cosyBatch.pollTimer) clearTimeout(state.cosyBatch.pollTimer);
}

function updateSidebarPips(base, produced, requested) {
  const row = sceneNavList.querySelector(`.scene-nav-item[data-base="${CSS.escape(base)}"] .nav-pips`);
  if (!row) return;
  const pips = row.querySelectorAll('.nav-pip');
  pips.forEach((pip, i) => {
    pip.classList.remove('done', 'active');
    if (i < produced) pip.classList.add('done');
    else if (i === produced) pip.classList.add('active');
  });
}

// ── Image batch (imagefx_runner --auto) ───────────────────────────────────

// Извлекает номер сцены из base-имени (scene_07 → 7). Нужно для --scenes
// флага runner'а, который принимает int индексы.
function sceneIndexFromBase(base) {
  const m = /(\d+)/.exec(base || '');
  return m ? parseInt(m[1], 10) : null;
}

async function startImageBatch() {
  if (state.imageBatch.active) return;

  const total = state.scenes.length;
  // Список сцен с номерами — для селекта в модалке и для понимания «чего нет».
  const scenesInfo = state.scenes
    .map(s => ({
      idx: sceneIndexFromBase(s.base),
      base: s.base,
      hasVariants: (s.variants || []).length > 0,
      preview: (s.text || s.prompt || '').slice(0, 50),
    }))
    .filter(s => s.idx != null)
    .sort((a, b) => a.idx - b.idx);

  const firstMissing = scenesInfo.find(s => !s.hasVariants);
  const defaultStart = firstMissing ? firstMissing.idx : 1;
  const missingCount = scenesInfo.filter(s => !s.hasVariants).length;

  // Options для селекта: "1 — уже готово" / "2 — (пусто)"
  const options = scenesInfo.map(s => {
    const tag = s.hasVariants ? ' ✓' : '';
    const preview = s.preview ? ` — ${escapeHtml(s.preview)}…` : '';
    const selected = s.idx === defaultStart ? 'selected' : '';
    return `<option value="${s.idx}" ${selected}>Сцена ${s.idx}${tag}${preview}</option>`;
  }).join('');

  const ok = await showModal({
    title: 'Сгенерировать картинки',
    bodyHtml: `
      Runner цепляется к <b>твоему Chrome</b> через CDP — чистый fingerprint,
      никаких следов automation. Flow-проект откроется сам, если вкладки нет.

      <div style="margin-top:14px">
        <label style="display:block; font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">
          Начать со сцены:
        </label>
        <select id="batch-start-scene" style="
          width: 100%;
          background: var(--bg-panel);
          color: var(--text);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 8px 10px;
          font-family: var(--font-sans);
          font-size: 0.9rem;
        ">${options}</select>
      </div>

      <label style="display: flex; gap: 8px; align-items: center; margin-top: 12px; cursor: pointer;">
        <input type="checkbox" id="batch-skip-done" checked style="cursor: pointer;">
        <span style="font-size: 0.88rem;">
          Пропускать сцены, у которых уже есть картинки (<b>${total - missingCount}</b>)
        </span>
      </label>

      <label style="display: flex; gap: 8px; align-items: flex-start; margin-top: 8px; cursor: pointer;">
        <input type="checkbox" id="batch-clean-session" style="cursor: pointer; margin-top: 3px;">
        <span style="font-size: 0.88rem;">
          Очистить cookies/Local Storage Google перед запуском
          <span style="display:block; color: var(--text-dim); font-size: 0.78rem; margin-top: 2px;">
            Сбрасывает trust-score Flow («unusual activity»). Придётся залогиниться заново.
          </span>
        </span>
      </label>

      <div class="mb-stats" style="margin-top:12px">
        <div class="mb-stat"><span class="mb-stat-label">Всего сцен</span><span class="mb-stat-num">${total}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">С картинками</span><span class="mb-stat-num">${total - missingCount}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">Пустых</span><span class="mb-stat-num">${missingCount}</span></div>
      </div>
      <div class="mb-note" style="margin-top:10px">
        Нужно: запущен <code>launch_chrome_debug.bat</code> и залогинен Google-аккаунт.
      </div>
    `,
    confirmText: 'Запустить Flow',
  });
  if (!ok) return;

  // Читаем выбор из модалки ДО того как откроется следующая (DOM ещё живой).
  const startInput = document.getElementById('batch-start-scene');
  const skipInput = document.getElementById('batch-skip-done');
  const cleanInput = document.getElementById('batch-clean-session');
  const startIdx = startInput ? parseInt(startInput.value, 10) : defaultStart;
  const skipDone = skipInput ? skipInput.checked : true;
  const cleanSession = cleanInput ? cleanInput.checked : false;

  // Фильтр: все сцены с index >= startIdx; при skipDone убираем те, где уже есть варианты
  const scenesFilter = scenesInfo
    .filter(s => s.idx >= startIdx)
    .filter(s => skipDone ? !s.hasVariants : true)
    .map(s => s.idx);

  if (!scenesFilter.length) {
    toast('После фильтрации ни одной сцены не осталось', 'error');
    return;
  }

  try {
    const res = await postJSON(
      `/api/images/${encodeURIComponent(state.scenario)}/regenerate-all`,
      { scenes: scenesFilter, clean_session: cleanSession },
    );
    toast(
      `imagefx запущен · ${scenesFilter.length} ${plural(scenesFilter.length, 'сцена', 'сцены', 'сцен')}: ${scenesFilter.slice(0, 8).join(', ')}${scenesFilter.length > 8 ? '…' : ''}`,
      'success',
    );

    const alreadyDone = scenesInfo.filter(s => s.hasVariants && !scenesFilter.includes(s.idx)).length;

    state.imageBatch = {
      active: true,
      total,
      done: alreadyDone,  // стартуем с уже готовых — прогресс-бар идёт вверх
      pollTimer: null,
      error: null,
      logTail: '',
      pid: res.pid,
      queueSize: scenesFilter.length,
      startScene: startIdx,
      skipDone,
    };
    renderSidebarAction();
    pollImageBatch();
  } catch (e) {
    toast(`Ошибка запуска: ${e.message}`, 'error');
  }
}

async function pollImageBatch() {
  if (!state.imageBatch.active) return;
  try {
    const url = `/api/images/${encodeURIComponent(state.scenario)}/imagefx-status`;
    const status = await fetchJSON(url);

    state.imageBatch.done = status.scenes_with_variants || 0;
    state.imageBatch.total = status.scenes_total || state.imageBatch.total;
    state.imageBatch.logTail = status.log_tail || '';

    if (status.failed) {
      state.imageBatch.active = false;
      state.imageBatch.error = status.error_hint || 'упал';
      toast(`Flow runner упал: ${state.imageBatch.error}`, 'error');
      renderSidebarAction();
      return;
    }

    if (status.done && !status.running) {
      state.imageBatch.active = false;
      toast(`Готово · ${state.imageBatch.done}/${state.imageBatch.total}`, 'success');
      renderSidebarAction();
      // Подтягиваем новые картинки в карточки
      await loadScenario(state.scenario, state.activeSceneBase);
      return;
    }

    renderSidebarAction();
    state.imageBatch.pollTimer = setTimeout(pollImageBatch, 3000);
  } catch (e) {
    console.warn('image batch poll error', e);
    state.imageBatch.pollTimer = setTimeout(pollImageBatch, 5000);
  }
}

function stopImageBatch() {
  state.imageBatch.active = false;
  if (state.imageBatch.pollTimer) clearTimeout(state.imageBatch.pollTimer);
  state.imageBatch.pollTimer = null;
}

function renderSidebarAction() {
  const slot = $('sb-action-slot');
  if (!slot) return;

  if (!state.scenes.length) {
    slot.innerHTML = '';
    return;
  }

  if (state.mode === 'image') {
    renderSidebarActionImage(slot);
    return;
  }

  if (state.mode === 'video') {
    renderSidebarActionVideo(slot);
    return;
  }

  const batch = state.cosyBatch;
  const total = state.scenes.length;
  const fullyDone = state.scenes.filter(
    s => (s.variants || []).length >= BATCH_META.variants
  ).length;
  const needsGen = total - fullyDone;

  let dataState, html;

  if (batch.active) {
    dataState = 'running';
    const pct = batch.total ? (batch.completed / batch.total) * 100 : 0;
    const currentIdx = state.scenes.findIndex(s => s.base === batch.currentBase);
    const currentNum = currentIdx >= 0 ? String(currentIdx + 1).padStart(3, '0') : '—';
    html = `
      <div class="sb-action-title">идёт генерация</div>
      <button class="sb-action-btn" data-action="cancel">
        <svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Прервать · ${batch.completed} / ${batch.total}</span>
          <span class="sb-action-btn-aux">сейчас ${currentNum} · ${batch.produced}/${batch.requested}</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>предложений <b>${batch.completed}</b>/${batch.total}</span>
        <span>вариантов <b>${batch.produced}</b>/${batch.requested}</span>
      </div>
    `;
  } else if (batch.error) {
    dataState = 'error';
    const pct = batch.total ? (batch.completed / batch.total) * 100 : 0;
    const errShort = (batch.error || '').slice(0, 48);
    html = `
      <div class="sb-action-title">ошибка на ${batch.currentBase || '—'}</div>
      <button class="sb-action-btn" data-action="restart">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Повторить</span>
          <span class="sb-action-btn-aux">${escapeHtml(errShort)}</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>сделано <b>${batch.completed}</b>/${batch.total}</span>
        <span>осталось ${batch.total - batch.completed}</span>
      </div>
    `;
  } else if (state.cosy.base) {
    // Одиночная перегенерация через CosyVoice — batch неактивен, но одна
    // сцена сейчас озвучивается. Приоритет выше, чем done/idle, чтобы
    // прогресс был виден независимо от общего состояния сценария.
    dataState = 'running';
    const base = state.cosy.base;
    const sc = state.scenes.find(s => s.base === base);
    const idx = state.scenes.findIndex(s => s.base === base);
    const num = idx >= 0 ? String(idx + 1).padStart(3, '0') : '—';
    const produced = (sc && sc.cosy) ? (sc.cosy.produced || 0) : 0;
    const requested = (sc && sc.cosy) ? (sc.cosy.requested || BATCH_META.variants) : BATCH_META.variants;
    const pct = requested ? (produced / requested) * 100 : 0;
    html = `
      <div class="sb-action-title">идёт перегенерация</div>
      <button class="sb-action-btn" disabled>
        <svg viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="5" width="4" height="14" rx="1"/>
          <rect x="14" y="5" width="4" height="14" rx="1"/>
        </svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Сцена ${num} · ${produced}/${requested}</span>
          <span class="sb-action-btn-aux">CosyVoice 3 · одна сцена</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>вариантов <b>${produced}</b>/${requested}</span>
        <span>остальные ${total - 1} в порядке</span>
      </div>
    `;
  } else if (needsGen === 0) {
    dataState = 'done';
    html = `
      <div class="sb-action-title">озвучка собрана</div>
      <button class="sb-action-btn" disabled>
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Готово · ${total}/${total}</span>
          <span class="sb-action-btn-aux">по ${BATCH_META.variants} вариантов на каждое</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: 100%"></div>
      </div>
      <div class="sb-action-meta">
        <span><b>${total}</b> предложений</span>
        <span>выбирай лучшие</span>
      </div>
    `;
  } else {
    dataState = 'idle';
    const pct = total ? (fullyDone / total) * 100 : 0;
    const etaMin = Math.ceil(needsGen * 45 / 60);
    html = `
      <div class="sb-action-title">массовая генерация</div>
      <button class="sb-action-btn" data-action="start">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Озвучить ${needsGen === total ? 'всё' : needsGen + ' ' + plural(needsGen, 'предложение', 'предложения', 'предложений')}</span>
          <span class="sb-action-btn-aux">CosyVoice 3 · ≈${etaMin} мин</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>готово <b>${fullyDone}</b>/${total}</span>
        <span>осталось <b>${needsGen}</b></span>
      </div>
    `;
  }

  slot.innerHTML = `<div class="sb-action" data-state="${dataState}">${html}</div>`;

  const btn = slot.querySelector('.sb-action-btn');
  if (btn && !btn.disabled) {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'start') startCosyBatch();
      else if (act === 'cancel') cancelCosyBatch();
      else if (act === 'restart') {
        state.cosyBatch.error = null;
        startCosyBatch();
      }
    });
  }
}

// ── Render action-slot для image-режима ───────────────────────────────────

function renderSidebarActionImage(slot) {
  const batch = state.imageBatch;
  const total = state.scenes.length;
  const withVariants = state.scenes.filter(s => (s.variants || []).length > 0).length;
  const missing = total - withVariants;

  let dataState, html;

  if (batch.active) {
    dataState = 'running';
    const done = batch.done;
    const tot = batch.total || total;
    const pct = tot ? (done / tot) * 100 : 0;
    html = `
      <div class="sb-action-title">идёт генерация Flow</div>
      <button class="sb-action-btn" disabled>
        <svg viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="5" width="4" height="14" rx="1"/>
          <rect x="14" y="5" width="4" height="14" rx="1"/>
        </svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Flow работает · ${done}/${tot}</span>
          <span class="sb-action-btn-aux">смотри Chrome-окно</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>сцен с картинками <b>${done}</b>/${tot}</span>
        <span>PID ${batch.pid || '—'}</span>
      </div>
    `;
  } else if (batch.error) {
    dataState = 'error';
    const done = batch.done;
    const tot = batch.total || total;
    const pct = tot ? (done / tot) * 100 : 0;
    html = `
      <div class="sb-action-title">flow упал</div>
      <button class="sb-action-btn" data-action="restart">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Запустить заново</span>
          <span class="sb-action-btn-aux">${escapeHtml((batch.error || '').slice(0, 40))}</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>сделано <b>${done}</b>/${tot}</span>
        <span>упал</span>
      </div>
    `;
  } else if (missing === 0 && total > 0) {
    dataState = 'done';
    html = `
      <div class="sb-action-title">картинки готовы</div>
      <button class="sb-action-btn" data-action="start">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Готово · ${total}/${total}</span>
          <span class="sb-action-btn-aux">перегенерировать всё</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: 100%"></div>
      </div>
      <div class="sb-action-meta">
        <span><b>${total}</b> сцен</span>
        <span>выбирай лучшие</span>
      </div>
    `;
  } else {
    dataState = 'idle';
    const pct = total ? (withVariants / total) * 100 : 0;
    const etaMin = Math.ceil(missing * 50 / 60);
    html = `
      <div class="sb-action-title">массовая генерация</div>
      <button class="sb-action-btn" data-action="start">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Сгенерировать ${missing === total ? 'все картинки' : missing + ' ' + plural(missing, 'сцену', 'сцены', 'сцен')}</span>
          <span class="sb-action-btn-aux">Google Flow · ≈${etaMin} мин</span>
        </span>
      </button>
      <div class="sb-action-bar">
        <div class="sb-action-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div class="sb-action-meta">
        <span>готово <b>${withVariants}</b>/${total}</span>
        <span>осталось <b>${missing}</b></span>
      </div>
    `;
  }

  slot.innerHTML = `<div class="sb-action" data-state="${dataState}">${html}</div>`;

  const btn = slot.querySelector('.sb-action-btn');
  if (btn && !btn.disabled) {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'start') startImageBatch();
      else if (act === 'restart') {
        state.imageBatch.error = null;
        startImageBatch();
      }
    });
  }
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

  // Стопим плеер ДО запроса: на Windows HTML5 <audio> держит open handle
  // на mp3, и бэкенд при unlink старого approved-файла падает с PermissionError
  // [WinError 32]. На бэке тоже есть retry-страховка, но проще отпустить файл
  // на стороне браузера.
  stopAudio();

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

// ── Video batch (video_runner.py) ─────────────────────────────────────────
// Логика зеркалит image-batch, но с поправками: Veo-генерация медленная
// (~80 сек/клип), сцены идут по одной, и таймауты тишины шире — 180 сек.

async function startVideoBatch() {
  if (!state.scenario) return;
  if (state.videoBatch.active) {
    toast('Видео-раннер уже запущен', 'info');
    return;
  }

  const total = state.scenes.length;
  const withClips = state.scenes.filter(s => (s.variants || []).length > 0).length;
  const missing = total - withClips;

  // Список сцен с номерами — для селекта «Начать со сцены». Зеркалит
  // image-batch: показываем индекс, флаг «есть клип», превью текста.
  const scenesInfo = state.scenes
    .map(s => ({
      idx: sceneIndexFromBase(s.base),
      base: s.base,
      hasVariants: (s.variants || []).length > 0,
      preview: (s.text || s.prompt || '').slice(0, 50),
    }))
    .filter(s => s.idx != null)
    .sort((a, b) => a.idx - b.idx);

  // По умолчанию стартуем с первой сцены без клипа — чтобы продолжить
  // прерванный прогон, а не запускать заново всё.
  const firstMissing = scenesInfo.find(s => !s.hasVariants);
  const defaultStart = firstMissing ? firstMissing.idx : 1;

  const options = scenesInfo.map(s => {
    const tag = s.hasVariants ? ' ✓' : '';
    const preview = s.preview ? ` — ${escapeHtml(s.preview)}…` : '';
    const selected = s.idx === defaultStart ? 'selected' : '';
    return `<option value="${s.idx}" ${selected}>Сцена ${s.idx}${tag}${preview}</option>`;
  }).join('');

  const ok = await showModal({
    title: 'Сгенерировать видео',
    bodyHtml: `
      Раннер цепляется к <b>твоему Chrome</b> через CDP (порт 9222).
      Flow откроется на проекте сценария, дальше скрипт сам загружает
      опорный кадр, вставляет промпт, ждёт Veo и скачивает mp4.

      <div style="margin-top:14px">
        <label style="display:block; font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">
          Начать со сцены:
        </label>
        <select id="video-batch-start-scene" style="
          width: 100%;
          background: var(--bg-panel);
          color: var(--text);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 8px 10px;
          font-family: var(--font-sans);
          font-size: 0.9rem;
        ">${options}</select>
      </div>

      <label style="display: flex; gap: 8px; align-items: center; margin-top: 12px; cursor: pointer;">
        <input type="checkbox" id="video-batch-skip-done" checked style="cursor: pointer;">
        <span style="font-size: 0.88rem;">
          Пропускать сцены, у которых уже есть клипы (<b>${withClips}</b>)
        </span>
      </label>

      <div class="mb-stats" style="margin-top:12px">
        <div class="mb-stat"><span class="mb-stat-label">Всего сцен</span><span class="mb-stat-num">${total}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">С клипами</span><span class="mb-stat-num">${withClips}</span></div>
        <div class="mb-stat"><span class="mb-stat-label">Пустых</span><span class="mb-stat-num">${missing}</span></div>
      </div>
      <div style="margin-top:14px">
        <div style="display:block; font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">
          Качество скачивания
        </div>
        <div style="display:flex; gap: 14px;">
          <label style="display:flex; gap:6px; align-items:center; cursor:pointer; font-size: 0.9rem;">
            <input type="radio" name="video-batch-quality" value="720p" checked style="cursor:pointer;">
            <span>720p <span style="color: var(--text-dim); font-size: 0.78rem;">(лёгкие файлы, быстрее)</span></span>
          </label>
          <label style="display:flex; gap:6px; align-items:center; cursor:pointer; font-size: 0.9rem;">
            <input type="radio" name="video-batch-quality" value="1080p" style="cursor:pointer;">
            <span>1080p <span style="color: var(--text-dim); font-size: 0.78rem;">(мастер-копия, ~2× вес)</span></span>
          </label>
        </div>
      </div>

      <label style="display: flex; gap: 8px; align-items: flex-start; margin-top: 12px; cursor: pointer;">
        <input type="checkbox" id="video-batch-clean-session" style="cursor: pointer; margin-top: 3px;">
        <span style="font-size: 0.88rem;">
          Очистить cookies/Local Storage Google перед запуском
          <span style="display:block; color: var(--text-dim); font-size: 0.78rem; margin-top: 2px;">
            Сбрасывает trust-score Flow («unusual activity»). Придётся залогиниться заново.
          </span>
        </span>
      </label>

      <div class="mb-note" style="margin-top:10px">
        Нужно: запущен <code>launch_chrome_debug.bat</code>, Google залогинен,
        Veo 3.1 выбран в Flow. Один клип ≈ 80 сек, на 23 сцены ≈ 30 минут.
      </div>
    `,
    confirmText: 'Запустить Veo',
  });
  if (!ok) return;

  // Читаем выбор из модалки до того как DOM удалится.
  const startInput = document.getElementById('video-batch-start-scene');
  const skipInput = document.getElementById('video-batch-skip-done');
  const cleanInput = document.getElementById('video-batch-clean-session');
  const qualityInput = document.querySelector('input[name="video-batch-quality"]:checked');
  const startIdx = startInput ? parseInt(startInput.value, 10) : defaultStart;
  const skipDone = skipInput ? skipInput.checked : true;
  const cleanSession = cleanInput ? cleanInput.checked : false;
  const quality = qualityInput ? qualityInput.value : '720p';

  // Фильтр сцен: всё начиная со startIdx; при skipDone выкидываем уже готовые.
  const scenesFilter = scenesInfo
    .filter(s => s.idx >= startIdx)
    .filter(s => skipDone ? !s.hasVariants : true)
    .map(s => s.idx);

  if (!scenesFilter.length) {
    toast('После фильтрации ни одной сцены не осталось', 'error');
    return;
  }

  try {
    const res = await postJSON(api().regenAll(state.scenario), {
      scenes: scenesFilter,
      clean_session: cleanSession,
      quality,
    });
    toast(
      `Video runner запущен · ${scenesFilter.length} ${plural(scenesFilter.length, 'сцена', 'сцены', 'сцен')}: ${scenesFilter.slice(0, 8).join(', ')}${scenesFilter.length > 8 ? '…' : ''} · ${quality}`,
      'success',
    );

    // Уже готовые (вне фильтра) учитываем как done — прогресс-бар идёт вверх.
    const alreadyDone = scenesInfo.filter(s => s.hasVariants && !scenesFilter.includes(s.idx)).length;

    state.videoBatch = {
      active: true,
      total,
      done: alreadyDone,
      clipsTotal: state.scenes.reduce((s, sc) => s + (sc.variants || []).length, 0),
      pollTimer: null,
      error: null,
      pid: res.pid,
      queueSize: scenesFilter.length,
      startScene: startIdx,
      skipDone,
    };
    renderSidebarAction();
    pollVideoBatch();
  } catch (e) {
    toast(`Ошибка запуска: ${e.message}`, 'error');
  }
}

async function pollVideoBatch() {
  if (!state.videoBatch.active) return;
  try {
    const status = await fetchJSON(api().runnerStatus(state.scenario));

    state.videoBatch.done = status.scenes_with_clips || 0;
    state.videoBatch.clipsTotal = status.clips_total || state.videoBatch.clipsTotal;

    if (status.failed) {
      state.videoBatch.active = false;
      state.videoBatch.error = 'video_runner быстро упал — смотри окно cmd';
      toast(state.videoBatch.error, 'error');
      renderSidebarAction();
      return;
    }

    if (status.done && !status.running) {
      state.videoBatch.active = false;
      toast(`Готово · клипов ${state.videoBatch.clipsTotal}`, 'success');
      renderSidebarAction();
      // Подтягиваем свежие mp4 в карточки сцен
      await loadScenario(state.scenario, state.activeSceneBase);
      return;
    }

    renderSidebarAction();
    state.videoBatch.pollTimer = setTimeout(pollVideoBatch, 5000);
  } catch (e) {
    console.warn('video batch poll error', e);
    state.videoBatch.pollTimer = setTimeout(pollVideoBatch, 7000);
  }
}

function stopVideoBatch() {
  state.videoBatch.active = false;
  if (state.videoBatch.pollTimer) clearTimeout(state.videoBatch.pollTimer);
  state.videoBatch.pollTimer = null;
}

function renderSidebarActionVideo(slot) {
  const batch = state.videoBatch;
  const total = state.scenes.length;
  const withClips = state.scenes.filter(s => (s.variants || []).length > 0).length;
  const missing = total - withClips;

  let dataState, html;

  if (batch.active) {
    dataState = 'running';
    const done = batch.done;
    const tot = batch.total || total;
    const pct = tot ? (done / tot) * 100 : 0;
    html = `
      <div class="sb-action-title">Veo рендерит</div>
      <button class="sb-action-btn" disabled>
        <svg viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="5" width="4" height="14" rx="1"/>
          <rect x="14" y="5" width="4" height="14" rx="1"/>
        </svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Veo работает · ${done}/${tot}</span>
          <span class="sb-action-btn-aux">смотри окно Chrome</span>
        </span>
      </button>
      <div class="sb-action-bar"><div class="sb-action-bar-fill" style="width: ${pct}%"></div></div>
      <div class="sb-action-meta">
        <span>сцен с клипами <b>${done}</b>/${tot}</span>
        <span>PID ${batch.pid || '—'}</span>
      </div>
    `;
  } else if (batch.error) {
    dataState = 'error';
    const tot = batch.total || total;
    const pct = tot ? (batch.done / tot) * 100 : 0;
    html = `
      <div class="sb-action-title">video_runner упал</div>
      <button class="sb-action-btn" data-action="restart">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Запустить заново</span>
          <span class="sb-action-btn-aux">${escapeHtml((batch.error || '').slice(0, 40))}</span>
        </span>
      </button>
      <div class="sb-action-bar"><div class="sb-action-bar-fill" style="width: ${pct}%"></div></div>
      <div class="sb-action-meta"><span>сделано <b>${batch.done}</b>/${tot}</span><span>упал</span></div>
    `;
  } else if (missing === 0 && total > 0) {
    dataState = 'done';
    html = `
      <div class="sb-action-title">все клипы готовы</div>
      <button class="sb-action-btn" data-action="start">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Готово · ${total}/${total}</span>
          <span class="sb-action-btn-aux">перегенерировать всё</span>
        </span>
      </button>
      <div class="sb-action-bar"><div class="sb-action-bar-fill" style="width: 100%"></div></div>
      <div class="sb-action-meta"><span><b>${total}</b> ${plural(total, 'сцена', 'сцены', 'сцен')}</span><span>выбирай дубли</span></div>
    `;
  } else {
    dataState = 'idle';
    const pct = total ? (withClips / total) * 100 : 0;
    const etaMin = Math.ceil(missing * 80 / 60);
    html = `
      <div class="sb-action-title">видео-раннер</div>
      <button class="sb-action-btn" data-action="start">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <span class="sb-action-btn-txt">
          <span class="sb-action-btn-main">Сгенерировать ${missing === total ? 'все видео' : missing + ' ' + plural(missing, 'сцену', 'сцены', 'сцен')}</span>
          <span class="sb-action-btn-aux">Veo 3.1 · ≈${etaMin} мин</span>
        </span>
      </button>
      <div class="sb-action-bar"><div class="sb-action-bar-fill" style="width: ${pct}%"></div></div>
      <div class="sb-action-meta"><span>готово <b>${withClips}</b>/${total}</span><span>осталось <b>${missing}</b></span></div>
    `;
  }

  slot.innerHTML = `<div class="sb-action sb-action-video" data-state="${dataState}">${html}</div>`;

  const btn = slot.querySelector('.sb-action-btn');
  if (btn && !btn.disabled) {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'start') startVideoBatch();
      else if (act === 'restart') {
        state.videoBatch.error = null;
        startVideoBatch();
      }
    });
  }
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

  // «Песнь целиком» — показываем только когда все сцены готовы
  renderFullSong();
}

// ── «Песнь целиком» — плеер full.mp3 в нижней части сайдбара ─────────────
//
// Появляется в voice-режиме когда у каждой сцены выбран вариант и нет
// сцен в статусе regen. Лениво генерирует превью через /api/full-preview
// (склейка из текущих selections), плеер инструмент только для прослушки —
// финальный full.mp3 пишется отдельно через «Собрать финал».

const fullSong = {
  audio: null,             // <Audio> instance (один на всё время сессии)
  loading: false,
  scenario: null,          // для какого сценария уже подгружена склейка
  snapshot: '',            // снимок selections на момент последней склейки
  sentenceCount: 0,        // сколько сегментов сейчас отрисовано
  sentenceStarts: [],      // [t₀, t₁, …] — реальные старты предложений в склейке (сек)
  sentenceDurations: [],   // длительности предложений (сек), для пропорций сегментов
};

// Снимок текущих выборов — если меняется, склейка устарела и нужна регенерация
function currentSelectionsSnapshot() {
  return state.scenes
    .map(s => `${s.base}:${s.selected || ''}:${s.status || ''}`)
    .join('|');
}

function renderFullSong() {
  const headerSong = document.getElementById('header-song');
  if (!headerSong) return;

  // Скрываем плеер: не voice, нет сцен, или ещё не все готовы
  const allDone = state.mode === 'voice'
    && state.scenes.length > 0
    && state.scenes.every(s => s.status === 'done');

  if (!allDone) {
    headerSong.hidden = true;
    stopFullSong();
    fullSong.sentenceCount = 0;
    return;
  }

  headerSong.hidden = false;

  // Перерисовываем сегменты при смене сценария или числа предложений —
  // чтобы сбросить inline-style flex (веса предыдущего мифа) на equal.
  const scenarioChanged = fullSong.scenario !== state.scenario;
  if (scenarioChanged || fullSong.sentenceCount !== state.scenes.length) {
    renderHeaderSongSegments(state.scenes.length);
    fullSong.sentenceCount = state.scenes.length;
  }

  // Если сменился сценарий, сбрасываем визуал плеера и тайминги
  // (audio.src + точные старты выставятся при следующем play через regenerate).
  if (fullSong.scenario !== state.scenario) {
    setFullSongPlaying(false);
    fullSong.sentenceStarts = [];
    fullSong.sentenceDurations = [];
    const cur = document.getElementById('header-song-cur');
    const tot = document.getElementById('header-song-tot');
    if (cur) cur.textContent = '00:00';
    if (tot) tot.textContent = '--:--';
    paintHeaderSongSegments(-1);
  }

  attachHeaderSongHandlers();
}

// Применяет пропорциональные ширины сегментов: каждый сегмент по flex
// получает «вес», равный длительности соответствующего предложения.
// До прихода данных от бэкенда сегменты — равномерные (flex: 1 1 0).
function applyHeaderSongSegmentWeights(durations) {
  const wrap = document.getElementById('header-song-segments');
  if (!wrap) return;
  const segs = wrap.querySelectorAll('.header-song-seg');
  if (segs.length !== durations.length) return;
  durations.forEach((d, i) => {
    // нижний порог 0.1 — гарантия видимости очень коротких предложений
    segs[i].style.flex = (Math.max(0.1, d)) + ' 1 0';
  });
}

// Раскладывает N сегментов (по одному на sentence_NN).
function renderHeaderSongSegments(n) {
  const wrap = document.getElementById('header-song-segments');
  if (!wrap) return;
  wrap.innerHTML = '';
  if (n <= 0) return;
  for (let i = 0; i < n; i++) {
    const el = document.createElement('div');
    el.className = 'header-song-seg';
    el.dataset.idx = i;
    wrap.appendChild(el);
  }
}

// Подсвечивает сегменты слева от текущего; -1 = очистить всё.
function paintHeaderSongSegments(currentIdx) {
  const wrap = document.getElementById('header-song-segments');
  if (!wrap) return;
  wrap.querySelectorAll('.header-song-seg').forEach((el, i) => {
    el.classList.toggle('passed', i < currentIdx);
    el.classList.toggle('current', i === currentIdx);
  });
}

// По времени t (сек) определяет 0-based индекс предложения.
// Если есть реальные старты с бэкенда — бинарный поиск по ним;
// иначе fallback на равномерную сетку.
function sentenceIdxForTime(t) {
  const starts = fullSong.sentenceStarts;
  if (starts && starts.length) {
    let lo = 0, hi = starts.length - 1, ans = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (starts[mid] <= t) { ans = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return ans;
  }
  const n = fullSong.sentenceCount;
  const dur = fullSong.audio && fullSong.audio.duration;
  if (!n || !dur) return 0;
  return Math.max(0, Math.min(n - 1, Math.floor((t / dur) * n)));
}

function attachHeaderSongHandlers() {
  const playBtn = document.getElementById('header-song-play');
  const segs = document.getElementById('header-song-segments');
  const tip  = document.getElementById('header-song-tip');
  if (!playBtn || !segs) return;
  if (playBtn.dataset.bound === '1') return; // обработчики ставим один раз
  playBtn.dataset.bound = '1';

  playBtn.onclick = async () => {
    // Пауза при повторном клике
    if (fullSong.audio && !fullSong.audio.paused) {
      fullSong.audio.pause();
      setFullSongPlaying(false);
      return;
    }
    // Глушим одиночное воспроизведение сцен — один источник звука за раз
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
    // Лениво пересобираем склейку: первый запуск, смена сценария,
    // или изменился набор выбранных вариантов.
    const stale = !fullSong.audio
      || !fullSong.audio.src
      || fullSong.scenario !== state.scenario
      || fullSong.snapshot !== currentSelectionsSnapshot();
    if (stale) {
      const ok = await regenerateFullSong();
      if (!ok) return;
    }
    try {
      await fullSong.audio.play();
      setFullSongPlaying(true);
    } catch (e) {
      console.error('full-song play failed', e);
      toast(`Не удалось запустить плеер: ${e.message}`, 'error');
    }
  };

  // Клик по сегменту — seek к началу соответствующего sentence_NN.
  // Если у нас есть реальные старты с бэкенда — берём их (точное попадание).
  // Иначе равномерная аппроксимация.
  segs.addEventListener('click', (e) => {
    const seg = e.target.closest('.header-song-seg');
    if (!seg) return;
    if (!fullSong.audio || !fullSong.audio.duration) return;
    const idx = parseInt(seg.dataset.idx, 10);
    const starts = fullSong.sentenceStarts;
    let target;
    if (starts && starts.length === fullSong.sentenceCount) {
      target = starts[idx];
    } else {
      const n = fullSong.sentenceCount || 1;
      target = (idx / n) * fullSong.audio.duration;
    }
    fullSong.audio.currentTime = target;
    updateFullSongTime();
  });

  // Hover показывает sentence_NNN над сегментом.
  segs.addEventListener('mousemove', (e) => {
    const seg = e.target.closest('.header-song-seg');
    if (!seg || !tip) { if (tip) tip.classList.remove('show'); return; }
    const idx = parseInt(seg.dataset.idx, 10);
    tip.textContent = 'sentence_' + String(idx + 1).padStart(3, '0');
    const wrapRect = segs.getBoundingClientRect();
    const segRect = seg.getBoundingClientRect();
    tip.style.left = (segRect.left - wrapRect.left + segRect.width / 2) + 'px';
    tip.classList.add('show');
  });
  segs.addEventListener('mouseleave', () => { if (tip) tip.classList.remove('show'); });
}

async function regenerateFullSong() {
  if (fullSong.loading) return false;
  fullSong.loading = true;
  const playBtn = document.getElementById('header-song-play');
  if (playBtn) playBtn.disabled = true;
  try {
    const res = await postJSON(
      `/api/full-preview/${encodeURIComponent(state.scenario)}`,
      {},
    );
    if (!res.ok) throw new Error(res.error || 'неизвестная ошибка');
    if (!fullSong.audio) {
      fullSong.audio = new Audio();
      fullSong.audio.preload = 'metadata';
      fullSong.audio.addEventListener('timeupdate', updateFullSongTime);
      fullSong.audio.addEventListener('ended', () => {
        setFullSongPlaying(false);
        const cur = document.getElementById('header-song-cur');
        if (cur) cur.textContent = '00:00';
        paintHeaderSongSegments(-1);
      });
      fullSong.audio.addEventListener('loadedmetadata', () => {
        const tot = document.getElementById('header-song-tot');
        if (tot) tot.textContent = formatFullSongTime(fullSong.audio.duration);
      });
    }
    fullSong.audio.src = res.url;
    fullSong.audio.load();
    fullSong.scenario = state.scenario;
    fullSong.snapshot = currentSelectionsSnapshot();
    // Реальные тайминги предложений в склейке (если бэкенд смог их посчитать).
    fullSong.sentenceStarts = Array.isArray(res.sentence_starts) ? res.sentence_starts : [];
    fullSong.sentenceDurations = Array.isArray(res.sentence_durations) ? res.sentence_durations : [];
    if (fullSong.sentenceDurations.length === fullSong.sentenceCount) {
      applyHeaderSongSegmentWeights(fullSong.sentenceDurations);
    }
    return true;
  } catch (e) {
    toast(`Не удалось склеить: ${e.message}`, 'error');
    return false;
  } finally {
    fullSong.loading = false;
    if (playBtn) playBtn.disabled = false;
  }
}

function updateFullSongTime() {
  if (!fullSong.audio) return;
  const cur = document.getElementById('header-song-cur');
  const t = fullSong.audio.currentTime || 0;
  if (cur) cur.textContent = formatFullSongTime(t);
  if (!fullSong.audio.duration) return;
  paintHeaderSongSegments(sentenceIdxForTime(t));
}

function setFullSongPlaying(playing) {
  const btn = document.getElementById('header-song-play');
  if (!btn) return;
  btn.classList.toggle('playing', playing);
  const svg = btn.querySelector('svg');
  if (svg) {
    svg.innerHTML = playing
      ? '<rect x="2.5" y="1" width="2.5" height="10"/><rect x="7" y="1" width="2.5" height="10"/>'
      : '<polygon points="2,1 11,6 2,11"/>';
  }
}

function stopFullSong() {
  if (fullSong.audio && !fullSong.audio.paused) {
    fullSong.audio.pause();
    setFullSongPlaying(false);
  }
}

function formatFullSongTime(s) {
  if (!s || isNaN(s)) return '--:--';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

// ── Copy prompt button ───────────────────────────────────────────────────
// Привязывает обработчик к кнопке копирования промпта внутри sceneDetail.
// На странице может быть только одна такая кнопка (id="copy-prompt-btn"),
// поэтому привязываемся по id.
function attachCopyPromptHandler(promptText) {
  const btn = $('copy-prompt-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(promptText);
      } else {
        const ta = document.createElement('textarea');
        ta.value = promptText;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      const label = btn.querySelector('span');
      const orig = label ? label.textContent : '';
      btn.classList.add('copied');
      if (label) label.textContent = 'Скопировано';
      setTimeout(() => {
        btn.classList.remove('copied');
        if (label) label.textContent = orig;
      }, 1500);
    } catch (e) {
      toast('Не удалось скопировать промпт', 'error');
    }
  });
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
const _publishBtn = $('publish-btn');
if (_publishBtn) _publishBtn.addEventListener('click', togglePublishedFromBottombar);
init().catch(e => toast('Ошибка инициализации: ' + e.message, 'error'));
