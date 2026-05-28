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
  // 'active' (не опубликовано) | 'archive' (только опубликовано) | 'all'
  // По умолчанию архив скрыт: опубликованные мифы не нужны в общем пуле,
  // но всегда доступны через сегмент «архив».
  hubFilter: 'active',
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
  if (state.mode === 'montage') {
    // У монтажа из API сейчас только список мифов (с прогрессом 4 шагов
    // pipeline'а). Остальные ручки появятся вместе с реальной интеграцией
    // build_<myth>.py / enrich_<myth>.py — пока на их месте no-op-toast,
    // см. renderHubDetail-ветку для montage.
    return {
      myths: '/api/montage/myths',
    };
  }
  return {
    myths: '/api/scenarios-summary',
    scenes:  (name) => `/api/scenes/${encodeURIComponent(name)}`,
    select:  (name) => `/api/select/${encodeURIComponent(name)}`,
    regen:   (name) => `/api/regenerate-cosyvoice/${encodeURIComponent(name)}`,
    regenEL: (name) => `/api/regenerate-elevenlabs/${encodeURIComponent(name)}`,
    finalize:(name) => `/api/finalize/${encodeURIComponent(name)}`,
    cosyBatchStart:  (name) => `/api/cosyvoice-batch-start/${encodeURIComponent(name)}`,
    cosyBatchStatus: (name) => `/api/cosyvoice-batch-status/${encodeURIComponent(name)}`,
  };
}

function modeLabel() {
  if (state.mode === 'image') return 'Ревью изображений';
  if (state.mode === 'video') return 'Ревью видео';
  if (state.mode === 'montage') return 'Монтаж';
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
  if (view === 'conveyor') {
    return { view: 'conveyor', scenario: parts[1] || null };
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
      setMode(['image', 'video', 'montage'].includes(route.mode) ? route.mode : 'voice');
      setView('hub');
      await loadHub();
      return true;
    }
    if (route.view === 'review' && route.scenario) {
      // У монтажа нет review-страницы (pipeline ещё в разработке) — любой
      // #review/montage/* хэш редиректим в его hub. Иначе loadScenario
      // упадёт на отсутствующем /api/montage/.../scenes.
      if (route.mode === 'montage') {
        setMode('montage');
        setView('hub');
        await loadHub();
        return true;
      }
      setMode(['image', 'video'].includes(route.mode) ? route.mode : 'voice');
      await loadScenario(route.scenario, route.sceneBase);
      setView('review');
      return true;
    }
    if (route.view === 'conveyor' && route.scenario) {
      // Конвейер монтажа всегда живёт в режиме montage. Если summaries
      // ещё не загружены (прямой заход по URL без хаба) — подтягиваем
      // их, чтобы renderConveyor смог взять display_name/статистику.
      setMode('montage');
      if (!state.summaries.length) {
        try { state.summaries = await fetchJSON(api().myths); } catch (_) {}
      }
      await openConveyor(route.scenario, { push: false });
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
  if (view === 'hub' || view === 'chooser' || view === 'conveyor') {
    stopAudio();
    if (typeof stopAllVideo === 'function') stopAllVideo();
    stopCosyProgress();
  }
  // Пишем минимальный hash для chooser/hub; review/conveyor пишут свои
  // hash отдельно (loadScenario / openConveyor — там известно имя сценария).
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
  // Параллельно подтягиваем статус CosyVoice-сервера. Не блокирующее:
  // если сервер недоступен — просто покажем кнопку «Запустить».
  refreshCosyServerStatus().catch(() => {});
}

// ── CosyVoice-сервер: статус-индикатор + кнопка запуска ────────────────────
//
// Сервер живёт отдельно (см. automation/cosyvoice_server.py), грузит модель
// один раз и обслуживает webapp по HTTP на 5001. Webapp поллит /health,
// чтобы показать пользователю состояние: офлайн / прогрев модели / готов.
//
// Состояния панели (data-state):
//   unknown — ещё не опросили (короткий миг при загрузке)
//   loading — идёт запрос /health
//   offline — сервер не отвечает (можно нажать «Запустить»)
//   warming — сервер живой, модель ещё грузится (~30 сек)
//   ready   — модель в памяти, можно жать «Озвучить»
//   error   — модель грузилась и упала (показываем причину)

let _cosyServerPollTimer = null;
let _cosyServerStartInFlight = false;

async function refreshCosyServerStatus() {
  const panel = document.getElementById('cosy-server-panel');
  if (!panel) return;
  const btn = document.getElementById('cosy-server-btn');
  const stopBtn = document.getElementById('cosy-server-stop-btn');
  const logBtn = document.getElementById('cosy-server-log-btn');

  let data;
  try {
    data = await fetchJSON('/api/cosyvoice-server/health');
  } catch (e) {
    setCosyState('error', `webapp не смог опросить /health: ${e.message}`);
    return;
  }

  // Управление видимостью кнопок: «Запустить» когда offline/error,
  // «стоп» и «логи» когда warming/ready (сервер живой).
  const isAlive = data.reachable && !data.model_error;
  if (btn) btn.hidden = isAlive;
  if (stopBtn) stopBtn.hidden = !isAlive;
  if (logBtn) logBtn.hidden = false; // лог всегда доступен — для разбора падений тоже

  if (!data.reachable) {
    setCosyState('offline', 'не запущен — нажми «Запустить»');
    return;
  }
  if (data.model_error) {
    setCosyState('error', `модель упала: ${data.model_error}`);
    if (btn) {
      btn.hidden = false;
      btn.textContent = 'Перезапустить';
    }
    return;
  }
  if (!data.model_loaded) {
    const uptime = Math.round(data.uptime_sec || 0);
    setCosyState('warming', `модель грузится… (${uptime}s)`);
    scheduleCosyPoll(2000);
    return;
  }
  // ready
  const queue = data.queue_len || 0;
  const queueText = queue > 0 ? ` · в очереди: ${queue}` : '';
  setCosyState('ready', `готов · аптайм ${Math.round(data.uptime_sec || 0)}s${queueText}`);
  // Когда сервер уже готов — опрашиваем реже (раз в 10 сек), чтобы
  // обновлять uptime/queue, но не насиловать сеть.
  scheduleCosyPoll(10000);
}

function setCosyState(state, subText) {
  const panel = document.getElementById('cosy-server-panel');
  const sub = document.getElementById('cosy-server-sub');
  if (panel) panel.dataset.state = state;
  if (sub) sub.textContent = subText;
}

function scheduleCosyPoll(ms) {
  if (_cosyServerPollTimer) clearTimeout(_cosyServerPollTimer);
  // Поллим только если chooser-страница ещё видна. На других экранах
  // индикатор скрыт, опрос не нужен.
  _cosyServerPollTimer = setTimeout(() => {
    if (document.body.dataset.view !== 'chooser') {
      _cosyServerPollTimer = null;
      return;
    }
    refreshCosyServerStatus().catch(() => {});
  }, ms);
}

async function onCosyServerStart() {
  if (_cosyServerStartInFlight) return;
  const btn = document.getElementById('cosy-server-btn');
  _cosyServerStartInFlight = true;
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Запускаю…';
  }
  setCosyState('loading', 'открываю окно cmd…');
  try {
    const res = await fetch('/api/cosyvoice-server/start', { method: 'POST' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    if (data.already_running) {
      toast('CosyVoice-сервер уже работает', 'info');
    } else {
      toast('Окно cmd открыто, модель грузится ~30 сек', 'info');
    }
    setCosyState('warming', 'модель грузится… (0s)');
    // Начинаем активный поллинг прогрева
    scheduleCosyPoll(2000);
  } catch (e) {
    setCosyState('error', `не удалось запустить: ${e.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Повторить';
      btn.hidden = false;
    }
  } finally {
    _cosyServerStartInFlight = false;
    if (btn) btn.disabled = false;
  }
}

async function onCosyServerStop() {
  if (!confirm('Остановить CosyVoice-сервер? Модель выгрузится из памяти.')) return;
  const stopBtn = document.getElementById('cosy-server-stop-btn');
  if (stopBtn) stopBtn.disabled = true;
  setCosyState('loading', 'останавливаю…');
  try {
    const res = await fetch('/api/cosyvoice-server/stop', { method: 'POST' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    toast(
      data.was_running ? `Сервер остановлен (PID ${data.pid})` : (data.message || 'Сервер уже не работал'),
      'info'
    );
  } catch (e) {
    toast(`Не удалось остановить: ${e.message}`, 'error');
  } finally {
    if (stopBtn) stopBtn.disabled = false;
    // Сразу опрашиваем — индикатор покажет offline, кнопки переключатся.
    refreshCosyServerStatus().catch(() => {});
  }
}

async function onCosyServerShowLog() {
  let data;
  try {
    data = await fetchJSON('/api/cosyvoice-server/log?lines=200');
  } catch (e) {
    toast(`Не смог прочитать лог: ${e.message}`, 'error');
    return;
  }
  showCosyLogModal(data);
}

function showCosyLogModal(data) {
  let modal = document.getElementById('cosy-log-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'cosy-log-modal';
    modal.className = 'cosy-log-modal';
    modal.innerHTML = `
      <div class="cosy-log-modal-dialog">
        <div class="cosy-log-modal-head">
          <h3 id="cosy-log-title">Лог CosyVoice-сервера</h3>
          <button id="cosy-log-close">Закрыть (Esc)</button>
        </div>
        <pre class="cosy-log-modal-body" id="cosy-log-body"></pre>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.dataset.open = '0';
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') modal.dataset.open = '0';
    });
    document.getElementById('cosy-log-close')
      .addEventListener('click', () => { modal.dataset.open = '0'; });
  }
  const title = document.getElementById('cosy-log-title');
  const body = document.getElementById('cosy-log-body');
  if (!data.exists) {
    title.textContent = 'Лог CosyVoice-сервера (файл не найден)';
    body.textContent = 'Лог-файл automation/_cosyvoice_server.log ещё не создан.\nЗапусти сервер хотя бы раз.';
  } else {
    const sizeKb = (data.size_bytes / 1024).toFixed(1);
    title.textContent = `Лог CosyVoice-сервера — ${data.path} (${sizeKb} KB)`;
    body.textContent = data.tail || '(пусто)';
    // Скроллим в конец — туда, где свежие строки.
    setTimeout(() => { body.scrollTop = body.scrollHeight; }, 0);
  }
  modal.dataset.open = '1';
}

document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('cosy-server-btn');
  if (startBtn) startBtn.addEventListener('click', onCosyServerStart);
  const stopBtn = document.getElementById('cosy-server-stop-btn');
  if (stopBtn) stopBtn.addEventListener('click', onCosyServerStop);
  const logBtn = document.getElementById('cosy-server-log-btn');
  if (logBtn) logBtn.addEventListener('click', onCosyServerShowLog);
});

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
  // Сегменты «в работе / архив / все». renderHubList сам подсветит
  // активный и обновит data-hub-mode на панели — здесь только маршрутизация.
  document.querySelectorAll('.hub-seg').forEach(seg => {
    seg.addEventListener('click', () => {
      if (state.hubFilter === seg.dataset.filter) return;
      state.hubFilter = seg.dataset.filter;
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
    const emptyLabel = {
      image: 'нет мифов с картинками',
      video: 'нет мифов с видео',
      montage: 'нет мифов, готовых к монтажу',
    }[state.mode] || 'нет мифов с озвучкой';
    $('hub-list-items').innerHTML = `<div class="hub-list-empty">${emptyLabel}</div>`;
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

// Что считать архивом. Раньше критерий был `published`, потом я переключил
// на `is_archived` (физическая локация content/архив/<миф>). Но между
// деплоем функционала и запуском миграции «опубликованные, но не
// перенесённые» мифы остаются на старых местах и попадают в «в работе»,
// что ломает ожидания пользователя. Сейчас критерий — ИЛИ-объединение:
// архивный = либо физически в content/архив/, либо помечен published.
// После миграции оба условия сходятся, отдельная семантика «архивно, но
// без флага» сохраняется (снятие публикации не возвращает миф в общий пул).
function isArchivedSummary(s) {
  return !!(s.is_archived || s.published);
}

function filterSummaries() {
  return state.summaries.filter(s => {
    const archived = isArchivedSummary(s);
    if (state.hubFilter === 'archive' && !archived) return false;
    if (state.hubFilter === 'active' && archived) return false;
    // 'all' — без фильтра по локации
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
  // В режиме монтажа критерий «готовности» — этап pipeline, а не доля
  // ревью. Подменяем подпись на «шаг N из 4», чтобы пользователю было
  // сразу понятно, что миф уже на конвейере.
  if (state.mode === 'montage') {
    const step = summary.montage_step ?? 0;
    const total = summary.montage_total_steps ?? 4;
    if (status === 'wip') return 'материалы ещё готовятся';
    if (step >= total) return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · мастер готов`;
    if (step === 0) return `${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')} · готов к сборке`;
    return `шаг ${step} из ${total} · ${scene_count} ${plural(scene_count, 'сцена', 'сцены', 'сцен')}`;
  }
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

// Часть сериала — имя содержит слэш И не относится к `архив/`.
// Используется для disabled-состояния кнопки publish: discovery работает
// на 2 уровнях, архив серии = 3 уровня, поддержки пока нет.
function isSeries(name) {
  if (!name || !name.includes('/')) return false;
  return !name.startsWith('архив/');
}

// Формат для архивной карточки: крупная пара день·месяц + год маленьким.
// Без иностранных букв и без сокращений — пусть типографика говорит сама.
function formatArchiveDate(iso) {
  if (!iso) return '<span class="ad-day">—</span>';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '<span class="ad-day">—</span>';
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `<span class="ad-day">${dd}·${mm}</span>${d.getFullYear()}`;
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

  // Синхронизируем сегменты: подсветка активного, счётчики по каждому режиму
  // (считаем от полного набора, без учёта search-фильтра — счётчики должны
  // отражать «сколько вообще есть», иначе будут прыгать при наборе текста).
  document.querySelectorAll('.hub-seg').forEach(seg => {
    seg.classList.toggle('active', seg.dataset.filter === state.hubFilter);
  });
  const counts = {
    active: state.summaries.filter(s => !isArchivedSummary(s)).length,
    archive: state.summaries.filter(s => isArchivedSummary(s)).length,
    all: state.summaries.length,
  };
  document.querySelectorAll('.hub-seg-n').forEach(el => {
    const k = el.dataset.count;
    if (k in counts) el.textContent = counts[k];
  });

  // «Настроение» панели: в режиме архива — тёплое золото, иначе нейтрально.
  // Атрибут читается из CSS — карточки и заливки переключаются автоматически.
  const panel = document.querySelector('.hub-list-panel');
  if (panel) panel.setAttribute('data-hub-mode', state.hubFilter);

  if (!filtered.length) {
    container.innerHTML = '<div class="hub-list-empty">ничего не найдено</div>';
    return;
  }

  const isArchive = state.hubFilter === 'archive';

  container.innerHTML = filtered.map((s) => {
    const globalIdx = state.summaries.findIndex(x => x.name === s.name);
    const active = s.name === state.hubSelectedName ? 'active' : '';
    const pubCls = s.published ? 'is-published' : '';
    // В режиме монтажа прогресс — это шаги pipeline (0–4), а не доля
    // отревьюенных сцен. Иначе in_progress-карточка с уже аппрувнутыми
    // voice/video показывала бы 100% бар, что вводит в заблуждение.
    const pct = state.mode === 'montage'
      ? ((s.montage_step || 0) / (s.montage_total_steps || 4)) * 100
      : (s.scene_count ? (s.done / s.scene_count) * 100 : 0);

    // В архиве — крупная дата справа вместо чипа. Дата = published_at, если
    // флаг публикации стоит; иначе короткая подпись «в архиве» (миф мог быть
    // вручную снят с публикации, но остался в content/архив/).
    // В режимах «в работе» / «все» опубликованный миф по-прежнему показывает
    // оранжевый чип «опуб.».
    const archived = isArchivedSummary(s);
    let rightCol;
    let extraCls = '';
    if (isArchive && archived) {
      rightCol = s.published
        ? `<div class="archive-date">${formatArchiveDate(s.published_at)}</div>`
        : `<div class="hub-item-status new">в архиве</div>`;
      extraCls = 'archive-card';
    } else if (s.published) {
      rightCol = `<div class="hub-item-status published">опуб.</div>`;
    } else if (s.status === 'in_progress') {
      rightCol = `<div class="hub-item-bar"><div class="hub-item-bar-fill" style="width:${pct}%"></div></div>`;
    } else {
      rightCol = `<div class="hub-item-status ${s.status}">${statusLabel(s.status)}</div>`;
    }

    return `
      <div class="hub-item status-${s.status} ${pubCls} ${extraCls} ${active}" data-name="${escapeAttr(s.name)}">
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
      // В режиме монтажа dblclick открывает конвейер мифа (4-ступенчатый
      // pipeline). Сами шаги пока заглушки — реальные ручки build/enrich/
      // stickers/bounce подключим позже.
      if (state.mode === 'montage') {
        openConveyor(el.dataset.name);
        return;
      }
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

  // ── Режим 04 · Монтаж — отдельная панель с 4-ступенчатым pipeline ────
  // Pipeline-инструменты (build_<myth>.py, enrich_<myth>.py, добавление
  // стикеров, bounce-анимация) ещё не интегрированы с webapp. Кнопка
  // «Открыть монтаж» пока показывает toast, что конвейер в разработке —
  // двойной клик по карточке мифа ведёт сюда же.
  if (state.mode === 'montage') {
    renderMontageHubDetail(container, summary);
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
      <button class="hub-btn hub-btn-publish ${summary.published ? 'is-on' : ''}"
              id="hub-publish-btn"
              title="${isSeries(summary.name)
                ? 'Пометить часть сериала опубликованной (без переноса в архив)'
                : 'Пометить миф опубликованным — папка переедет в content/архив/'}">
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

// ── Режим 04 · Монтаж: детальная панель с 4-ступенчатым pipeline ──────────
//
// Бэкенд (/api/montage/myths) уже считает montage_step (0–4). Здесь
// рисуем визуализацию: трубу из 4 модулей-карточек, статистику входа
// (аппрув voice/video), прогресс-бар, CTA «Открыть монтаж».
//
// Pipeline-инструменты пока не подключены — кнопка CTA и dblclick по
// карточке мифа показывают toast. Когда build/enrich/stickers/bounce
// получат API-ручки, заменим toast на навигацию в conveyor-страницу.

const MONTAGE_STEPS = [
  {
    key: 'skeleton',
    title: 'Скелет',
    tag: 'build',
    desc: 'Импорт аппрув-аудио, аппрув-видео и музыки. Видео тянется под голос (стретч до границы кадра 60fps). Интро-капс + karaoke-разметка.',
  },
  {
    key: 'transitions',
    title: 'Переходы и звуки',
    tag: 'enrich',
    desc: 'CapCut-переходы между сценами (whoosh / paper / zoom) с правильной громкостью SFX. План тянется из эталона Мидаса.',
  },
  {
    key: 'stickers',
    title: 'Стикеры и звуки',
    tag: 'stickers',
    desc: 'Эталонные стикеры (по 2 идеи A/B на сцену) на свою сцену + SFX из канона Каллисто.',
  },
  {
    key: 'bounce',
    title: 'Анимация стикеров',
    tag: 'bounce',
    desc: 'Растягиваем каждый стикер на сцену и добавляем циклическую качку y ±0.07 каждые 300 мс.',
  },
];

function renderMontageHubDetail(container, summary) {
  const globalIdx = state.summaries.findIndex(x => x.name === summary.name);
  const roman = toRoman(globalIdx + 1);
  const stepDone = Math.max(0, Math.min(4, summary.montage_step || 0));
  const totalSteps = summary.montage_total_steps || 4;
  // Активный шаг — следующий после последнего done. Если все 4 готовы,
  // активного нет (pipeline завершён).
  const stepActive = stepDone < totalSteps ? stepDone + 1 : null;
  const pct = Math.round((stepDone / totalSteps) * 100);

  // CTA-текст и кнопка зависят от состояния:
  //   step 0 + status=wip — материалы ещё не аппрувлены
  //   step 0 + status=ready — можно собирать скелет
  //   step 1–3 — продолжить следующим шагом
  //   step 4 — мастер готов, можно пересобрать
  let ctaText, ctaBtnLabel;
  if (summary.status === 'wip') {
    ctaText = `<b>Материалы ещё не аппрувлены.</b> Закройте сначала ревью озвучки и видео — без этого pipeline нечем кормить.`;
    ctaBtnLabel = 'Открыть монтаж';
  } else if (stepDone === 0) {
    ctaText = `<b>Готово к старту.</b> Аудио и видео аппрувлены, можно собирать скелет (шаг 1 из ${totalSteps}).`;
    ctaBtnLabel = 'Начать монтаж';
  } else if (stepDone < totalSteps) {
    ctaText = `<b>Шаг ${stepDone} из ${totalSteps} готов.</b> Дальше — ${MONTAGE_STEPS[stepDone].title.toLowerCase()}.`;
    ctaBtnLabel = `Перейти к шагу ${stepDone + 1}`;
  } else {
    ctaText = `<b>Мастер готов.</b> Все 4 шага pipeline'а пройдены, видео лежит в content/final/.`;
    ctaBtnLabel = 'Открыть конвейер';
  }

  // Прогрессивная градиент-линия между ступенями — заполнена до stepDone.
  // Считаем в процентах ширины: от первой ступени к четвёртой, шаг = 33.3%.
  const fillPct = stepDone === 0 ? 0 : (stepDone - 1) * (100 / (totalSteps - 1)) +
                                       (stepActive !== null ? 12 : 0);

  const stepsHtml = MONTAGE_STEPS.map((step, idx) => {
    const stepNum = idx + 1;
    let stateCls = 'locked';
    if (stepNum <= stepDone) stateCls = 'done';
    else if (stepNum === stepActive) stateCls = 'active';
    return `
      <div class="mh-step ${stateCls}">
        <div class="mh-step-ring">${stateCls === 'done' ? '✓' : stepNum}</div>
        <div class="mh-step-name">${escapeHtml(step.title)}</div>
        <div class="mh-step-tag">${escapeHtml(step.tag)}</div>
        <div class="mh-step-desc">${escapeHtml(step.desc)}</div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="hub-dp-eyebrow">
      <span>Миф · ${roman}</span>
      <span class="dossier-id">${escapeHtml(summary.name)}</span>
    </div>

    <h1 class="hub-dp-title">${escapeHtml(summary.display_name)}.</h1>
    <p class="hub-dp-subtitle">
      Конвейер собирает CapCut-проект из ревью-аппрува: скелет → переходы →
      стикеры → анимация. На каждом шаге можно остановиться и подправить
      вручную.
    </p>

    <div class="hub-dp-stats">
      <div class="hub-dp-stat good">
        <div class="hub-dp-stat-label">видео аппрув</div>
        <div class="hub-dp-stat-value">${summary.done}<span class="unit">/${summary.scene_count}</span></div>
      </div>
      <div class="hub-dp-stat">
        <div class="hub-dp-stat-label">шотов всего</div>
        <div class="hub-dp-stat-value">${summary.approved_count}</div>
      </div>
      <div class="hub-dp-stat accent">
        <div class="hub-dp-stat-label">длина мастера</div>
        <div class="hub-dp-stat-value" style="font-size:1.3rem"><span style="font-size:0.9em">${formatDuration(summary.scene_count * 2.5)}</span></div>
      </div>
      <div class="hub-dp-stat ${summary.regen ? 'warn' : ''}">
        <div class="hub-dp-stat-label">шаг pipeline</div>
        <div class="hub-dp-stat-value">${stepDone}<span class="unit">/${totalSteps}</span></div>
      </div>
    </div>

    <div class="hub-dp-progress">
      <div class="hub-dp-progress-head">
        <div class="hub-dp-progress-label">прогресс pipeline</div>
        <div class="hub-dp-progress-pct">${pct}%</div>
      </div>
      <div class="hub-dp-bar">
        <div class="hub-dp-bar-fill ${stepDone >= totalSteps ? 'good' : ''}" style="width:${pct}%"></div>
      </div>
    </div>

    <div class="hub-dp-scenes-head">
      <div class="hub-dp-scenes-title">4 ступени конвейера</div>
      <div class="hub-dp-legend">
        <span><span class="dot done"></span>готов</span>
        <span><span class="dot mint"></span>сейчас</span>
        <span><span class="dot pending"></span>ждёт</span>
      </div>
    </div>

    <div class="mh-steps" style="--mh-fill:${fillPct}%">
      ${stepsHtml}
    </div>

    <div class="hub-dp-cta">
      <div class="hub-dp-cta-text">${ctaText}</div>
      <button class="hub-btn hub-btn-primary" id="hub-open-btn">
        ${ctaBtnLabel}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
      </button>
    </div>
  `;

  const openBtn = $('hub-open-btn');
  if (openBtn) {
    // Открываем конвейер даже когда status='wip'. Сама страница уже
    // существует (с заглушечными CTA внутри ступеней) — пользователь
    // может посмотреть pipeline, даже если входы ещё не аппрувлены.
    openBtn.addEventListener('click', () => openConveyor(summary.name));
  }
}

// ── Конвейер монтажа: открытие страницы pipeline по выбранному мифу ──────
//
// Самодостаточная страница (см. .conveyor-container и .cv-* в style.css).
// Кнопки внутри шагов пока заглушки (toast'ы) — реальные API-ручки
// build/enrich/stickers/bounce подключим позже. Здесь только маршрутизация
// и рендер визуального состояния шагов по `montage_step` из summary.

async function openConveyor(scenario, { push = true } = {}) {
  if (push) pushHash(['conveyor', scenario]);
  else writeHash(['conveyor', scenario]);
  setMode('montage');
  setView('conveyor');
  // Если summaries ещё не подъехали (прямой заход по URL без хаба) —
  // дотягиваем их сейчас, чтобы renderConveyor не упёрся в «миф не найден».
  if (!state.summaries.length) {
    try { state.summaries = await fetchJSON('/api/montage/myths'); }
    catch (_) {}
  }
  try {
    renderConveyor(scenario);
  } catch (err) {
    console.error('renderConveyor failed:', err);
    const c = $('conveyor-container');
    if (c) c.innerHTML = `
      <div style="padding:48px;color:#f55b5b;font-family:monospace;font-size:0.9rem">
        <div style="margin-bottom:12px;color:#dddad5;font-size:1.1rem">Ошибка рендера конвейера</div>
        <pre style="white-space:pre-wrap">${escapeHtml(err && err.stack || String(err))}</pre>
      </div>
    `;
  }
}

function renderConveyor(scenario) {
  const container = $('conveyor-container');
  if (!container) return;
  const summary = (state.summaries || []).find(s => s.name === scenario);
  if (!summary) {
    container.innerHTML = `
      <div class="cv-shell">
        <div class="cv-topbar">
          <div class="cv-brand-row">
            <button class="cv-brand" id="cv-brand-back">КИСЫ ОЛИМПА</button>
            <div class="cv-crumb">
              <button id="cv-crumb-hub">Монтаж</button>
              <span class="sep">/</span>
              <b>${escapeHtml(scenario)}</b>
            </div>
          </div>
          <div class="cv-topcenter">миф <em>не найден</em> в списке монтажа</div>
          <div></div>
        </div>
        <div class="cv-body">
          <main class="cv-pipeline">
            <div class="cv-pipe-inner">
              <p style="color:var(--text-dim);font-family:var(--font-mono);font-size:0.8rem">
                Сценарий «${escapeHtml(scenario)}» не найден в списке монтажа.
              </p>
            </div>
          </main>
        </div>
      </div>
    `;
    wireConveyorBackHandlers();
    return;
  }

  const totalSteps = summary.montage_total_steps || 4;
  const stepDone = Math.max(0, Math.min(totalSteps, summary.montage_step || 0));
  const stepActive = stepDone < totalSteps ? stepDone + 1 : null;
  const pct = Math.round((stepDone / totalSteps) * 100);

  // Master timecode — пока пересчёт из количества сцен (как в renderMontageHubDetail).
  // Когда build_<myth>.py начнёт класть фактическую длину мастера в JSON,
  // подменим на реальное значение.
  const masterDur = formatDuration(summary.scene_count * 2.5);
  // Стандартное «MM:SS.mmm» — для отображения в плашке MASTER рядом.
  const masterDisplay = masterDur + '.000';

  // SVG-кольцо прогресса для топбара: длина окружности r=9 → 2πr ≈ 56.5.
  const ringDash = 56.5;
  const ringOffset = ringDash * (1 - pct / 100);

  // Градиент трубы между ступенями — заполнен до stepDone.
  const pipeGradient = buildConveyorPipeGradient(stepDone, totalSteps);

  // «Аппрув. аудио» — sentence-уровень из approved_sentences/, а не
  // видео-done. Бэкенд отдаёт audio_done; fallback на summary.done
  // нужен только для старых клиентов/респонсов без поля.
  const approvedAudio = summary.audio_done ?? summary.done ?? 0;
  const approvedShots = summary.approved_count ?? summary.done ?? 0;

  container.innerHTML = `
    <div class="cv-shell">

      <div class="cv-topbar">
        <div class="cv-brand-row">
          <button class="cv-brand" id="cv-brand-back" title="К выбору режима">КИСЫ ОЛИМПА</button>
          <div class="cv-crumb">
            <button id="cv-crumb-hub">Монтаж</button>
            <span class="sep">/</span>
            <b>${escapeHtml(summary.display_name)}</b>
          </div>
        </div>
        <div class="cv-topcenter">сборка <em>CapCut</em>-проекта · конвейер 4 ступени</div>
        <div class="cv-brand-row" style="gap:14px">
          <div class="cv-tc-master">
            <span class="lbl">MASTER</span>
            <b>${escapeHtml(masterDisplay)}</b>
          </div>
          <div class="cv-progress-pill">
            <div class="cv-progress-ring">
              <svg width="22" height="22" viewBox="0 0 22 22">
                <circle class="track" cx="11" cy="11" r="9"/>
                <circle class="fill" cx="11" cy="11" r="9"
                        stroke-dasharray="${ringDash}" stroke-dashoffset="${ringOffset.toFixed(2)}"/>
              </svg>
            </div>
            <div class="cv-progress-text"><b>${stepDone}</b> / ${totalSteps} шага</div>
          </div>
        </div>
      </div>

      <div class="cv-body">
        <main class="cv-pipeline">
          <div class="cv-pipe-inner">

            <header class="cv-pipe-head">
              <div class="cv-pipe-head-left">
                <div class="eyebrow">
                  <button class="back" id="cv-back-list">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
                    к списку мифов
                  </button>
                  <span>сборка / pipeline / capcut</span>
                </div>
                <h1>${renderConveyorTitle(summary.display_name)}</h1>
                <div class="sub">
                  ${summary.scene_count} ${plural(summary.scene_count, 'сцена', 'сцены', 'сцен')},
                  ${approvedShots} ${plural(approvedShots, 'аппрув-шот', 'аппрув-шота', 'аппрув-шотов')}.
                  Конвейер собирает CapCut-проект из ревью-аппрува — на каждом
                  шаге можно остановиться и подправить вручную.
                </div>
              </div>
              <div class="cv-pipe-stats">
                <div class="cv-pipe-stat">
                  <div class="v ${approvedAudio > 0 ? 'green' : ''}">${approvedAudio}</div>
                  <div class="l">аппрув. аудио</div>
                </div>
                <div class="cv-pipe-stat">
                  <div class="v ${approvedShots > 0 ? 'green' : ''}">${approvedShots}</div>
                  <div class="l">аппрув. шотов</div>
                </div>
                <div class="cv-pipe-stat">
                  <div class="v mint">${masterDur}</div>
                  <div class="l">длина</div>
                </div>
                <div class="cv-pipe-stat">
                  <div class="v">${stepDone}<span style="color:var(--text-ghost)">/${totalSteps}</span></div>
                  <div class="l">шаг pipeline</div>
                </div>
              </div>
            </header>

            <div style="margin: 0 0 22px; display:flex; align-items:center; gap:12px;">
              <div style="flex:1; height:3px; background: var(--border); border-radius: 2px; overflow:hidden; position:relative;">
                <div style="position:absolute; inset:0; width:${pct}%; background: linear-gradient(90deg, var(--green), var(--mint)); border-radius: 2px; transition: width 0.4s;"></div>
              </div>
              <div style="font-family: var(--font-mono); font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-ghost);">
                прогресс pipeline · <span style="color: var(--mint)">${pct}%</span>
              </div>
            </div>

            <div class="cv-steps" style="--cv-pipe-fill: ${pipeGradient}">
              ${renderConveyorSteps(summary, stepDone, stepActive, totalSteps)}
            </div>

          </div>
        </main>
      </div>
    </div>
  `;

  wireConveyorBackHandlers();
  wireConveyorStepButtons(summary);
  loadConveyorTransitions(summary.name);
}

// Подтягивает реальные переходы из живого CapCut-драфта мифа и заполняет
// план на шаге 2 (плашка «Переходов выбрано» + сетка стыков). Если драфт
// ещё не собран (шаг 1 не запускался) — показываем нейтральную заглушку.
async function loadConveyorTransitions(scenario) {
  const mount = $('cv-trans-preview');
  const countEl = $('cv-trans-count');
  if (!mount) return;
  let data;
  try {
    data = await fetchJSON(`/api/montage/${encodeURIComponent(scenario)}/transitions`);
  } catch (_) {
    mount.innerHTML = '<span class="cv-trans-empty">не удалось прочитать драфт</span>';
    return;
  }
  if (!data || !data.ready || !(data.transitions || []).length) {
    mount.innerHTML = '<span class="cv-trans-empty">скелет не собран — запусти шаг 1</span>';
    if (countEl) countEl.textContent = '—';
    return;
  }
  const chips = data.transitions.map(t => {
    const isCut = t.label === 'Cut';
    const dur = (t.duration != null) ? ` · ${t.duration.toFixed(2)}` : '';
    return `<span class="cv-trans-chip ${isCut ? '' : 'picked'}"><span class="dot"></span>${t.from}→${t.to} ${escapeHtml(t.label)}${dur}</span>`;
  });
  mount.innerHTML = chips.join('');
  if (countEl) countEl.textContent = `${data.picked}/${data.total}`;
}

// Линейный градиент для соединительной трубы между ступенями: зелёным
// заливаем долю готовых шагов, мятным — текущий активный, серым — остаток.
function buildConveyorPipeGradient(stepDone, totalSteps) {
  const donePct = (stepDone / totalSteps) * 100;
  const activeEnd = stepDone < totalSteps ? donePct + (100 / totalSteps) : donePct;
  return `linear-gradient(180deg,
    var(--green) 0%,
    var(--green) ${donePct.toFixed(1)}%,
    var(--mint) ${donePct.toFixed(1)}%,
    var(--mint) ${activeEnd.toFixed(1)}%,
    var(--border) ${activeEnd.toFixed(1)}%,
    var(--border) 100%)`;
}

// Имя мифа в h1: «Дионис и Ариадна.» → последнее слово курсивом-мятным
// (паттерн из мокапа). Без второго слова — просто эскейпим целиком.
function renderConveyorTitle(displayName) {
  const safe = escapeHtml(displayName);
  const parts = displayName.split(' ');
  if (parts.length < 2) return safe + '.';
  const last = escapeHtml(parts.pop());
  const rest = escapeHtml(parts.join(' '));
  return `${rest} <em>${last}</em>.`;
}

// 4 ступени конвейера — структура повторяет мокап. Состояние шага:
//   done   — stepNum <= stepDone
//   active — stepNum === stepActive
//   locked — иначе
// Текущая реализация рисует фиктивные данные валидации/превью — заменим
// их на реальные, когда подключим API скелета/переходов/стикеров/баунса.
const CV_STEPS = [
  {
    num: 1,
    title: 'Скелет',
    tag: 'build',
    runner: 'build_<myth>.py',
    desc: 'Импорт аппрув-аудио, аппрув-видео и музыки в CapCut. Видео тянется под голос (стретч до границы кадра 60fps). Сразу прибиты <em>интро-капс субтитры</em> и karaoke-разметка.',
    eta: '~4 s · 5 дорожек',
  },
  {
    num: 2,
    title: 'Переходы и <em>звуки</em>',
    tag: 'enrich',
    runner: 'enrich_<myth>.py',
    desc: 'Расставляем CapCut-переходы между сценами (<code>whoosh</code>, <code>paper-bag</code>, <code>swish</code>) с правильной громкостью SFX. План тянется из эталона Мидаса — можно перетыкать прямо здесь до запуска.',
    eta: '~3.2 s · переходы + SFX',
  },
  {
    num: 3,
    title: 'Стикеры и звуки',
    tag: 'stickers',
    runner: 'add_stickers.py',
    desc: 'Эталонные стикеры (по 2 идеи A/B на сцену) кладутся на свою сцену как заготовка на всю длину. Каждому стикеру свой SFX из канона Каллисто — <code>Pac=0.39</code>, <code>coin=0.28</code>, <code>ding=1.00</code>.',
    eta: '26 эталонов · 14 каркасов',
  },
  {
    num: 4,
    title: 'Анимация стикеров',
    tag: 'bounce',
    runner: 'animate_stickers.py',
    desc: 'Растягиваем каждый стикер на всю сцену и добавляем циклическую качку <code>y ±0.07</code> каждые <code>300 мс</code>. Перед этим даём вам удалить/заменить лишние стикеры руками в draft_content.json.',
    eta: 'y±0.07 · 300 мс · per-clip',
  },
];

function renderConveyorSteps(summary, stepDone, stepActive, totalSteps) {
  return CV_STEPS.map(step => {
    let stateCls = 'locked';
    if (step.num <= stepDone) stateCls = 'done';
    else if (step.num === stepActive) stateCls = 'active';
    return renderConveyorStep(step, stateCls, summary);
  }).join('');
}

function renderConveyorStep(step, stateCls, summary) {
  const statusBlock = stateCls === 'done'
    ? `<span class="dot"></span><b>готов</b><span>· сохранён</span>`
    : stateCls === 'active'
      ? `<span class="dot"></span><b>готов к запуску</b>`
      : `<span class="dot"></span><span>заблокирован шагом ${step.num - 1}</span>`;

  const preview = renderConveyorStepPreview(step, summary);
  const validate = renderConveyorStepValidate(step, stateCls, summary);

  // На шаге 1 «Редактор плана» доступен всегда (и до запуска, и после).
  // На шаге 2 «Редактор переходов» доступен, как только собран скелет
  // (шаг не заблокирован) — переходы пишутся прямо в CapCut-драфт.
  const editPlanBtn = step.num === 1
    ? `<button class="cv-step-btn ghost" data-cv-action="edit-plan" data-step="${step.num}">Редактор плана</button>`
    : (step.num === 2 && stateCls !== 'locked')
      ? `<button class="cv-step-btn ghost" data-cv-action="edit-plan" data-step="${step.num}">Редактор переходов</button>`
      : '';

  const ctaRow = stateCls === 'done'
    ? `
        <button class="cv-step-btn done">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6 9 17l-5-5"/></svg>
          <span class="stack">собрано<small>${escapeHtml(step.runner)}</small></span>
        </button>
        <button class="cv-step-btn ghost" data-cv-action="rerun" data-step="${step.num}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9"/><path d="m3 3 9 9"/></svg>
          Пересобрать
        </button>
        ${editPlanBtn}
        <button class="cv-step-btn ghost" data-cv-action="open-capcut" data-step="${step.num}">открыть в CapCut</button>
        <div class="cv-step-meta">${escapeHtml(step.runner)} · ${escapeHtml(step.eta)}</div>
      `
    : stateCls === 'active'
      ? `
        <button class="cv-step-btn primary" data-cv-action="run" data-step="${step.num}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5,3 19,12 5,21" fill="currentColor" stroke="none"/></svg>
          <span class="stack">Запустить шаг ${step.num}<small>${escapeHtml(step.runner)}</small></span>
        </button>
        ${editPlanBtn}
        <div class="cv-step-meta">${escapeHtml(step.eta)}</div>
      `
      : `
        <button class="cv-step-btn" disabled>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>
          <span class="stack">Запустить шаг ${step.num}<small>${escapeHtml(step.runner)}</small></span>
        </button>
        <div class="cv-step-meta">${escapeHtml(step.eta)}</div>
      `;

  return `
    <article class="cv-step ${stateCls}">
      <div class="badge"><div class="ring"><span>${step.num}</span></div></div>
      <div class="card">
        <div class="cv-step-head">
          <div class="cv-step-title">
            <h3>${step.title}</h3>
            <span class="tag">${escapeHtml(step.tag)}</span>
          </div>
          <div class="cv-step-status">${statusBlock}</div>
        </div>
        <div class="cv-step-desc">${step.desc}</div>
        ${validate}
        ${preview}
        <div class="cv-step-cta-row">${ctaRow}</div>
      </div>
    </article>
  `;
}

function renderConveyorStepValidate(step, stateCls, summary) {
  // Заглушки: пока показываем фиктивные значения. Заменим на реальные
  // когда API монтажа начнёт отдавать состояние входов pipeline'а.
  if (step.num === 1) {
    return `
      <div class="cv-validate">
        <div class="cv-val ok"><div class="ic"></div><div class="text">Аудио sentence<small>elevenlabs/cosyvoice</small></div><div class="count">${summary.audio_done ?? summary.done ?? 0}/${summary.audio_total ?? summary.scene_count}</div></div>
        <div class="cv-val ok"><div class="ic"></div><div class="text">Видео шоты<small>Veo / approved</small></div><div class="count">${summary.approved_count}/${summary.scene_count}</div></div>
        <div class="cv-val ok"><div class="ic"></div><div class="text">Музыка<small>thinking_island.mp3</small></div><div class="count">1/1</div></div>
        <div class="cv-val ok"><div class="ic"></div><div class="text">Интро капс<small>«${escapeHtml(summary.display_name)}.»</small></div><div class="count">ok</div></div>
      </div>
    `;
  }
  if (step.num === 2) {
    return `
      <div class="cv-validate">
        <div class="cv-val ok"><div class="ic"></div><div class="text">Переходов выбрано<small>из CapCut-драфта</small></div><div class="count" id="cv-trans-count">${Math.max(0, summary.scene_count - 1)}/${Math.max(0, summary.scene_count - 1)}</div></div>
      </div>
    `;
  }
  if (step.num === 3) {
    return `
      <div class="cv-validate">
        <div class="cv-val ${stateCls === 'locked' ? 'miss' : 'ok'}"><div class="ic"></div><div class="text">Переходы<small>шаг 2</small></div><div class="count">${stateCls === 'locked' ? '—' : 'готов'}</div></div>
        <div class="cv-val ok"><div class="ic"></div><div class="text">Эталонные стикеры<small>A/B на сцену</small></div><div class="count">${summary.scene_count * 2}</div></div>
        <div class="cv-val ok"><div class="ic"></div><div class="text">SFX канон Каллисто<small>Pac/coin/ding</small></div><div class="count">ok</div></div>
      </div>
    `;
  }
  // step 4
  return `
    <div class="cv-validate">
      <div class="cv-val ${stateCls === 'locked' ? 'miss' : 'ok'}"><div class="ic"></div><div class="text">Стикеры размещены<small>шаг 3</small></div><div class="count">${stateCls === 'locked' ? '—' : 'готов'}</div></div>
      <div class="cv-val ok"><div class="ic"></div><div class="text">Паттерн качки<small>y ±0.07 / 300мс</small></div><div class="count">канон</div></div>
    </div>
  `;
}

function renderConveyorStepPreview(step, summary) {
  if (step.num === 1) {
    // Превью «5 дорожек собрано» убрано — оно дублировало плашки
    // валидации сверху и занимало место без новой информации.
    return '';
  }
  if (step.num === 2) {
    // План переходов между сценами — реальные стыки из живого CapCut-драфта
    // (заполняет loadConveyorTransitions). До ответа сервера — заглушка.
    return `
      <div class="cv-step-preview">
        <div class="cv-step-preview-title">план переходов · из CapCut</div>
        <div class="cv-trans-preview" id="cv-trans-preview">
          <span class="cv-trans-empty">загрузка переходов из драфта…</span>
        </div>
      </div>
    `;
  }
  if (step.num === 3) {
    const sticks = [
      ['📱', 'iMessage'], ['⭐', 'Rating 5★'], ['💳', 'Payment'],
      ['🔔', 'Notif'], ['📊', 'Stats'], ['💬', 'Comment'],
      ['🎯', 'Target'], ['🏆', 'Trophy'], ['📈', 'Chart up'],
      ['🔥', 'Streak'], ['💎', 'Premium'], ['🎮', 'Tinder'],
      ['✅', 'Done'], ['⚡', 'Boost'],
    ];
    const items = sticks.map(([e, l]) =>
      `<div class="cv-stick locked"><div class="emoji">${e}</div>${escapeHtml(l)}</div>`
    ).join('');
    return `
      <div class="cv-step-preview">
        <div class="cv-step-preview-title">эталон A · ${sticks.length} стикеров</div>
        <div class="cv-stick-preview">${items}</div>
      </div>
    `;
  }
  // step 4 — паттерн качки
  return `
    <div class="cv-step-preview">
      <div class="cv-step-preview-title">паттерн качки</div>
      <div class="cv-skeleton-tracks">
        <div class="cv-skel-track subs">
          <div class="lbl">y-offset</div>
          <div class="strip" style="background:repeating-linear-gradient(90deg, var(--mint-dim) 0 12px, transparent 12px 16px);"></div>
        </div>
      </div>
    </div>
  `;
}

function wireConveyorBackHandlers() {
  const brand = $('cv-brand-back');
  if (brand) brand.addEventListener('click', () => {
    if (_currentDepth > 0) history.go(-_currentDepth);
    else goToChooser();
  });
  const crumb = $('cv-crumb-hub');
  if (crumb) crumb.addEventListener('click', () => goBack(['hub', 'montage']));
  const back = $('cv-back-list');
  if (back) back.addEventListener('click', () => goBack(['hub', 'montage']));
}

function wireConveyorStepButtons(summary) {
  // Шаги 2-4 пока заглушки — реальные ручки появятся вместе с
  // automation/conveyor/step_2_enrich.py и далее. Шаг 1 уже подключён.
  document.querySelectorAll('.conveyor-container [data-cv-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.cvAction;
      const stepNum = btn.dataset.step;
      if (action === 'run' && stepNum === '1') {
        runMontageStep1(summary, btn);
        return;
      }
      if (action === 'rerun' && stepNum === '1') {
        runMontageStep1(summary, btn, { force: true });
        return;
      }
      if (action === 'edit-plan' && stepNum === '1') {
        openPlanEditor(summary);
        return;
      }
      if (action === 'edit-plan' && stepNum === '2') {
        openTransitionEditor(summary);
        return;
      }
      const label = {
        run: `Запуск шага ${stepNum}`,
        rerun: `Пересборка шага ${stepNum}`,
        'edit-plan': `Редактор плана шага ${stepNum}`,
        'open-capcut': 'Открытие в CapCut',
      }[action] || `Действие "${action}"`;
      toast(`${label} — пока заглушка, ручка ещё не подключена`);
    });
  });
}

// ═══════════════════════════════════════════════════════════════════
// РЕДАКТОР ПЛАНА · макет А (компактный)
// ═══════════════════════════════════════════════════════════════════
// Открывается из cv-step (шаг 1, action="edit-plan"). Грузит метаданные
// шотов из /api/montage/<scenario>/plan, рисует таблицу-партитуру с
// inline-слайдерами для start_from и speed_override. Сохраняет тем же
// endpoint'ом POST'ом, опционально — сразу запускает шаг 1.
//
// Структура состояния редактора живёт в this-closure, без глобалок —
// модалка создаётся и удаляется на каждое открытие.

// step="any" — нативный <input type="range"> работает с float-разрешением
// браузера (~10000 шагов на трек), что выглядит как непрерывное движение.
// Численное значение для отображения и сохранения округляется до 2 знаков.
const PLAN_START_STEP = 'any';
const PLAN_SPEED_MIN = 0.5;
const PLAN_SPEED_MAX = 2.0;
const PLAN_SPEED_STEP = 'any';

async function openPlanEditor(summary) {
  // Старая открытая модалка должна закрыться раньше — на случай повторного клика.
  document.getElementById('plan-editor-overlay')?.remove();

  // Показываем skeleton-плашку пока ждём fetch.
  const overlay = document.createElement('div');
  overlay.id = 'plan-editor-overlay';
  overlay.className = 'pe-overlay';
  overlay.innerHTML = `
    <div class="pe-shell">
      <div class="pe-loading">
        <div class="pe-spinner"></div>
        <div>Считаю длительности видео и голоса…</div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  // Закрытие по клику на фон (но не на саму shell)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closePlanEditor();
  });
  // ESC закрывает
  const onEsc = (e) => { if (e.key === 'Escape') closePlanEditor(); };
  document.addEventListener('keydown', onEsc);
  overlay.dataset.escHandler = '1';
  overlay._escHandler = onEsc;

  let meta;
  try {
    const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/plan`);
    const data = await res.json();
    if (!data.ok) {
      overlay.querySelector('.pe-shell').innerHTML = `<div class="pe-error">Не удалось загрузить план:<br>${escapeHtml(data.message || '???')}</div>`;
      return;
    }
    meta = data;
  } catch (e) {
    overlay.querySelector('.pe-shell').innerHTML = `<div class="pe-error">Ошибка сети: ${escapeHtml(e.message)}</div>`;
    return;
  }

  // state — мутируем по слайдерам/дропдауну, сохраняем разом в save().
  // Ключ — scene_key (scene_03), значения совпадают с plan.json shot-entry.
  //
  // variant храним ВСЕГДА фактически выбранную версию (для сцен с >1 версией).
  // Иначе «вернул на v1» не отличить от «не трогал» — и патч не приведёт
  // драфт к v1, если там уже стоит v2 (баг рассинхрона драфта и плана).
  const state = { shots: {} };
  for (const scene of meta.scenes) {
    for (const shot of scene.shots) {
      const hasVariants = shot.variants && shot.variants.length > 1;
      state.shots[shot.scene_key] = {
        start_from: shot.start_from || 0,
        speed_override: shot.speed_override ?? null,
        variant: hasVariants ? shot.variant : null,
        default_variant: hasVariants ? shot.variants[0].variant : null,
      };
    }
  }

  overlay.querySelector('.pe-shell').innerHTML = renderPlanEditorShell(summary, meta);
  wirePlanEditor(overlay, summary, meta, state);
}

function closePlanEditor() {
  const ov = document.getElementById('plan-editor-overlay');
  if (!ov) return;
  if (ov._escHandler) document.removeEventListener('keydown', ov._escHandler);
  ov.classList.add('pe-out');
  setTimeout(() => ov.remove(), 160);
}

function renderPlanEditorShell(summary, meta) {
  // Сумма длительностей голоса = длина мастера.
  const masterUs = meta.scenes.reduce((s, sc) => s + (sc.voice_span_us || 0), 0);
  const masterStr = formatDuration(masterUs / 1_000_000);

  const rowsHtml = meta.scenes.map(scene => renderPlanEditorScene(scene)).join('');

  return `
    <header class="pe-head">
      <div class="pe-head-left">
        <div class="pe-bcrumb">сборка / pipeline / capcut / <em>редактор плана</em></div>
        <h2>Редактор <i>плана</i> · <span class="pe-step">шаг 1</span>
          <small>${escapeHtml(summary.display_name)} · ${meta.scenes.length} сцен · ${meta.total_shots} шотов</small>
        </h2>
      </div>
      <div class="pe-head-meta">
        <div><b>${escapeHtml(masterStr)}</b><span>длина мастера</span></div>
        <div><b class="pe-mint" data-pe-edited-count>${meta.edited_count}</b><span>правок</span></div>
        <div><b>${meta.total_shots}/${meta.total_shots}</b><span>шотов</span></div>
      </div>
      <button class="pe-close" title="Закрыть (Esc)">×</button>
    </header>

    <div class="pe-toolbar">
      <span class="pe-lbl">фильтр</span>
      <button class="pe-chip is-on" data-pe-filter="all">всё (${meta.total_shots})</button>
      <button class="pe-chip" data-pe-filter="edited">только правки (<span data-pe-edited-count>${meta.edited_count}</span>)</button>
      <span class="pe-grow"></span>
      <button class="pe-ghost" data-pe-action="reset-all">⟲ сбросить всё</button>
    </div>

    <div class="pe-grid-head">
      <span>#</span>
      <span>sentence + текст</span>
      <span>видеошот</span>
      <span>старт &nbsp;·&nbsp; 0.0 — N.N s</span>
      <span>скорость &nbsp;·&nbsp; 0.5 — 2.0 ×</span>
      <span style="text-align:center">скраб</span>
      <span style="text-align:center" title="Применить / сбросить эту сцену">⟳ ↺</span>
    </div>
    <div class="pe-rows">${rowsHtml}</div>

    <footer class="pe-footer">
      <span class="pe-summary">
        <b data-pe-edited-count>${meta.edited_count}</b> правок ·
        ${meta.total_shots - meta.edited_count} на автомате
      </span>
      <span class="pe-grow"></span>
      <button class="pe-btn pe-btn-secondary" data-pe-action="cancel">Отменить</button>
      <button class="pe-btn pe-btn-secondary" data-pe-action="save">Сохранить план</button>
      <button class="pe-btn pe-btn-primary" data-pe-action="save-and-run">▶ Сохранить и запустить шаг 1</button>
    </footer>
  `;
}

function renderPlanEditorScene(scene) {
  // Цитата = первый sentence (если их несколько, склеиваем).
  const quote = scene.audios.map(a => a.text).filter(Boolean).join(' ').slice(0, 90);
  const sentLabel = scene.audios.map(a => a.sent).join(' + ');
  // Один ряд = один shot. Если в сцене 2 шота, второй ряд показывает «↳» вместо номера.
  return scene.shots.map((shot, idx) => {
    const isFirst = idx === 0;
    const target = shot.target_duration_s ?? '?';
    const src = shot.src_duration_s ?? '?';
    const maxStart = computeMaxStart(shot);  // максимальный старт-сдвиг в секундах
    const startInit = shot.start_from || 0;
    const speedInit = shot.speed_override ?? shot.auto_speed ?? 1.0;
    const variants = shot.variants || [];
    const variantOverridden = variants.length > 1 && shot.variant !== variants[0].variant;
    const isEdited = startInit > 0 || shot.speed_override !== null || variantOverridden;
    const variantsJson = escapeHtml(JSON.stringify(variants));
    // Дропдаун версий показываем только если их больше одной.
    const variantSelect = variants.length > 1
      ? `<select class="pe-variant" data-variant title="Версия видеошота (у версий разная длина)">
           ${variants.map(v => `<option value="${v.variant}" ${v.variant === shot.variant ? 'selected' : ''}>${v.variant} · ${v.duration_s != null ? v.duration_s.toFixed(1) + 's' : '?'}</option>`).join('')}
         </select>`
      : `<span class="pe-variant-single">${shot.variant}</span>`;
    return `
      <div class="pe-row ${isEdited ? 'is-edited' : ''}"
           data-scene-key="${escapeHtml(shot.scene_key)}"
           data-max-start="${maxStart.toFixed(3)}"
           data-target-s="${(shot.target_duration_s || 0).toFixed(3)}"
           data-src-s="${(shot.src_duration_s || 0).toFixed(3)}"
           data-auto-speed="${(shot.auto_speed || 1).toFixed(3)}"
           data-default-variant="${variants[0] ? variants[0].variant : ''}"
           data-variants='${variantsJson}'>
        <span class="pe-sid">${isFirst ? scene.sid : '<span class="pe-cont">↳</span>'}</span>
        <span class="pe-sent">
          ${isFirst ? `<b>${escapeHtml(sentLabel)}</b> <span class="pe-dur">${scene.voice_span_s.toFixed(1)} s</span>` : '<span class="pe-dim">··· (та же сцена)</span>'}
          ${isFirst && quote ? `<em class="pe-preview">${escapeHtml(quote)}${quote.length >= 90 ? '…' : ''}</em>` : ''}
        </span>
        <span class="pe-shot">
          <span class="pe-shot-top">
            <span class="pe-shot-name">${escapeHtml(scene.shots.length > 1 ? shot.scene_key : shot.file.replace(/\.(mp4|webm|mov)$/i, ''))}</span>
            ${variantSelect}
          </span>
          <span class="pe-shot-src" data-shot-src>src ${typeof src === 'number' ? src.toFixed(1) : src} s → ${target.toFixed ? target.toFixed(1) : target} s</span>
        </span>
        <span class="pe-ctrl">
          <input type="range" data-kind="start"
                 min="0" max="${maxStart.toFixed(3)}" step="${PLAN_START_STEP}"
                 value="${startInit.toFixed(3)}"
                 ${maxStart <= 0 ? 'disabled' : ''}>
          <span class="pe-val ${startInit > 0 ? 'pe-mint' : 'pe-auto'}" data-val="start">
            ${maxStart <= 0 ? '—' : startInit.toFixed(2) + ' s'}
          </span>
        </span>
        <span class="pe-ctrl">
          <input type="range" data-kind="speed"
                 min="${PLAN_SPEED_MIN}" max="${PLAN_SPEED_MAX}" step="${PLAN_SPEED_STEP}"
                 value="${speedInit.toFixed(3)}">
          <span class="pe-val ${shot.speed_override !== null ? 'pe-mint' : 'pe-auto'}" data-val="speed">
            ${shot.speed_override !== null ? speedInit.toFixed(2) + '×' : 'auto · ' + (shot.auto_speed || 1).toFixed(2) + '×'}
          </span>
        </span>
        <span class="pe-scrub">
          <span class="pe-scrub-full"></span>
          <span class="pe-scrub-window"></span>
          <span class="pe-scrub-marker"></span>
        </span>
        <span class="pe-rowactions">
          <button class="pe-apply" data-pe-apply title="Применить только эту сцену к собранному проекту (без полной пересборки)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9"/><path d="m3 3 9 9"/></svg>
          </button>
          <button class="pe-reset-row" data-pe-reset title="Сбросить правки этой сцены (старт = 0, скорость = авто)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 2v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L3 8"/></svg>
          </button>
        </span>
      </div>`;
  }).join('');
}

// max_start: сколько секунд можно «съесть» с начала видео.
// Раньше ограничивали `src - target`, чтобы оставшийся хвост точно покрывал
// голос. Сейчас разрешаем сдвинуться вплоть до `src - 0.1s` — если хвоста
// не хватит, build_skeleton автоматически замедлит видео (speed = хвост/target),
// и UI динамически сдвигает правый ползунок скорости в эту позицию.
function computeMaxStart(shot) {
  const src = shot.src_duration_s || 0;
  // Минимум 0.1с оставляем под хвост — иначе source_timerange схлопнется в 0.
  return Math.max(0, +(src - 0.1).toFixed(2));
}

// auto_speed для текущего start_from (логика build_skeleton):
//   eff_src = src - start_from
//   если eff_src >= target → speed = 1.0 (обрезка)
//   иначе                  → speed = eff_src / target (замедление)
function computeAutoSpeed(srcS, targetS, startS) {
  if (srcS <= 0 || targetS <= 0) return 1.0;
  const eff = Math.max(0.01, srcS - startS);
  return eff >= targetS ? 1.0 : eff / targetS;
}

function wirePlanEditor(overlay, summary, meta, state) {
  // ── Слайдеры на каждом ряду ──
  overlay.querySelectorAll('.pe-row').forEach(row => {
    const key = row.dataset.sceneKey;
    const targetS = parseFloat(row.dataset.targetS);
    const defaultVariant = row.dataset.defaultVariant || '';
    let variants = [];
    try { variants = JSON.parse(row.dataset.variants || '[]'); } catch { variants = []; }

    // srcS/maxStart МЕНЯЮТСЯ при смене версии видео (разная длина).
    let srcS = parseFloat(row.dataset.srcS);
    let maxStart = parseFloat(row.dataset.maxStart);

    const inputs = row.querySelectorAll('input[type="range"]');
    const startInput = inputs[0];
    const speedInput = inputs[1];
    const valStart = row.querySelector('[data-val="start"]');
    const valSpeed = row.querySelector('[data-val="speed"]');
    const scrub = row.querySelector('.pe-scrub');
    const variantSelect = row.querySelector('[data-variant]');
    const shotSrcLabel = row.querySelector('[data-shot-src]');

    // userTouchedSpeed = true как только пользователь сам двинул ползунок
    // скорости. Пока false — слайдер «приклеен» к auto-значению и сдвигается
    // вместе со start. Сбрасывается на «Reset all».
    let userTouchedSpeed = state.shots[key].speed_override !== null;
    speedInput.addEventListener('input', () => { userTouchedSpeed = true; });

    // ── Смена версии видеошота (другой файл → другая длина) ──
    if (variantSelect) {
      variantSelect.addEventListener('change', () => {
        const v = variantSelect.value;
        const vm = variants.find(x => x.variant === v);
        const newSrc = vm && vm.duration_s != null ? vm.duration_s : srcS;
        srcS = newSrc;
        maxStart = Math.max(0, +(srcS - 0.1).toFixed(2));
        startInput.max = maxStart.toFixed(3);
        if (parseFloat(startInput.value) > maxStart) startInput.value = maxStart.toFixed(3);
        startInput.disabled = maxStart <= 0;
        if (shotSrcLabel) {
          shotSrcLabel.textContent = `src ${srcS.toFixed(1)} s → ${targetS.toFixed(1)} s`;
        }
        // Храним ВСЕГДА фактически выбранную версию (даже дефолтную), чтобы
        // патч точно привёл драфт к ней. «edited»-подсветка — отдельно.
        state.shots[key].variant = v;
        refresh();
      });
    }

    function refresh() {
      const cur = state.shots[key];
      const startVal = parseFloat(startInput.value);
      const dynamicAuto = computeAutoSpeed(srcS, targetS, startVal);

      // Если юзер не трогал скорость — приклеиваем ползунок к auto.
      if (!userTouchedSpeed) {
        speedInput.value = dynamicAuto.toString();
      }
      const speedSrc = parseFloat(speedInput.value);

      // speed_override = null когда значение совпадает с текущим auto.
      const speedVal = (!userTouchedSpeed || Math.abs(speedSrc - dynamicAuto) < 0.001)
        ? null
        : speedSrc;

      cur.start_from = startVal;
      cur.speed_override = speedVal;

      // Подпись старта
      if (maxStart <= 0) {
        valStart.textContent = '—';
      } else {
        valStart.textContent = startVal.toFixed(2) + ' s';
      }
      valStart.classList.toggle('pe-mint', startVal > 0);
      valStart.classList.toggle('pe-auto', startVal === 0);

      // Подпись скорости — auto показывает актуальный auto (с учётом start),
      // ручное значение показывает само себя.
      if (speedVal === null) {
        valSpeed.textContent = `auto · ${dynamicAuto.toFixed(2)}×`;
        valSpeed.classList.add('pe-auto');
        valSpeed.classList.remove('pe-mint');
      } else {
        valSpeed.textContent = speedVal.toFixed(2) + '×';
        valSpeed.classList.remove('pe-auto');
        valSpeed.classList.add('pe-mint');
      }

      // variant считается правкой только если отличается от дефолтной версии.
      const variantEdited = cur.variant != null && cur.variant !== defaultVariant;
      const isEdited = startVal > 0 || speedVal !== null || variantEdited;
      row.classList.toggle('is-edited', isEdited);

      // Скраб: окно начинается с start_from. Его длина в source-секундах =
      // target × effSpeed (если auto<1 → окно уже = target×auto = хвост).
      if (scrub && srcS > 0) {
        const effSpeed = speedVal === null ? dynamicAuto : speedVal;
        const windowSrcDur = Math.min(srcS - startVal, targetS * effSpeed);
        const startPct = (startVal / srcS) * 100;
        const widthPct = Math.max(0, (windowSrcDur / srcS) * 100);
        const win = scrub.querySelector('.pe-scrub-window');
        const mk = scrub.querySelector('.pe-scrub-marker');
        win.style.left = startPct + '%';
        win.style.width = widthPct + '%';
        mk.style.left = startPct + '%';
      }
      updateEditedCount(overlay, state);
    }
    // refresh-чейн: start двигает speed (если auto), speed двигает только подпись.
    startInput.addEventListener('input', refresh);
    speedInput.addEventListener('input', refresh);
    // Reset (двойной клик на val) — сбрасываем userTouchedSpeed.
    valSpeed.addEventListener('dblclick', () => {
      userTouchedSpeed = false;
      refresh();
    });
    refresh();

    // Возврат версии к дефолтной (первой) — для reset.
    function resetVariant() {
      if (variantSelect && defaultVariant) {
        variantSelect.value = defaultVariant;
        const vm = variants.find(x => x.variant === defaultVariant);
        srcS = vm && vm.duration_s != null ? vm.duration_s : srcS;
        maxStart = Math.max(0, +(srcS - 0.1).toFixed(2));
        startInput.max = maxStart.toFixed(3);
        startInput.disabled = maxStart <= 0;
        if (shotSrcLabel) shotSrcLabel.textContent = `src ${srcS.toFixed(1)} s → ${targetS.toFixed(1)} s`;
        // Явно фиксируем дефолтную версию (а не null), чтобы патч привёл
        // драфт обратно к ней, если там стоит другая.
        state.shots[key].variant = defaultVariant;
      } else {
        state.shots[key].variant = null;
      }
    }

    // Экспортируем refresh, чтобы reset-all мог вызвать его после смены value.
    row._refresh = refresh;
    row._resetUserSpeed = () => { userTouchedSpeed = false; };
    row._resetVariant = resetVariant;

    // ── Точечное применение этой сцены к собранному проекту ──
    const applyBtn = row.querySelector('[data-pe-apply]');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => applyPlanShot(summary, key, state, applyBtn));
    }

    // ── Сброс правок только этой строки (старт=0, скорость=авто, версия=дефолт) ──
    const resetBtn = row.querySelector('[data-pe-reset]');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        startInput.value = '0';
        userTouchedSpeed = false;
        resetVariant();
        refresh();
      });
    }
  });

  // ── Фильтр-чипсы ──
  overlay.querySelectorAll('.pe-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      overlay.querySelectorAll('.pe-chip').forEach(c => c.classList.remove('is-on'));
      chip.classList.add('is-on');
      const filter = chip.dataset.peFilter;
      overlay.querySelectorAll('.pe-row').forEach(row => {
        const edited = row.classList.contains('is-edited');
        row.style.display = (filter === 'edited' && !edited) ? 'none' : '';
      });
    });
  });

  // ── Reset-all: вернуть start=0, скорость auto, версию к дефолтной.
  overlay.querySelector('[data-pe-action="reset-all"]').addEventListener('click', () => {
    overlay.querySelectorAll('.pe-row').forEach(row => {
      const startInput = row.querySelector('input[data-kind="start"]');
      startInput.value = '0';
      if (row._resetUserSpeed) row._resetUserSpeed();
      if (row._resetVariant) row._resetVariant();
      if (row._refresh) row._refresh();
    });
  });

  // ── Закрытие ──
  overlay.querySelector('.pe-close').addEventListener('click', closePlanEditor);
  overlay.querySelector('[data-pe-action="cancel"]').addEventListener('click', closePlanEditor);

  // ── Сохранить ──
  overlay.querySelector('[data-pe-action="save"]').addEventListener('click', async () => {
    await savePlanState(summary, state);
    toast('План сохранён в content/<миф>/montage/plan.json', 'success');
    closePlanEditor();
  });

  // ── Сохранить и запустить шаг 1 ──
  overlay.querySelector('[data-pe-action="save-and-run"]').addEventListener('click', async (e) => {
    const ok = await savePlanState(summary, state);
    if (!ok) return;
    closePlanEditor();
    // Симулируем клик по «Запустить шаг 1» в существующей карточке шага.
    const runBtn = document.querySelector('[data-cv-action="run"][data-step="1"]')
                || document.querySelector('[data-cv-action="rerun"][data-step="1"]');
    if (runBtn) runBtn.click();
    else toast('План сохранён, но не нашёл кнопку «Запустить шаг 1». Нажми вручную.', 'warn');
  });
}

function updateEditedCount(overlay, state) {
  const n = Object.values(state.shots).filter(
    s => (s.start_from > 0) || (s.speed_override !== null)
      || (s.variant != null && s.variant !== s.default_variant)
  ).length;
  overlay.querySelectorAll('[data-pe-edited-count]').forEach(el => { el.textContent = n; });
}

// Точечный патч одного шота в уже собранном CapCut-проекте.
// Не пересобирает весь шаг 1 — меняет только source/speed одного сегмента.
async function applyPlanShot(summary, shotKey, state, btn) {
  if (btn.dataset.busy === '1') return;
  const cur = state.shots[shotKey] || { start_from: 0, speed_override: null, variant: null };
  btn.dataset.busy = '1';
  btn.classList.add('is-busy');
  try {
    const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/patch-shot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shot_key: shotKey,
        start_from: cur.start_from || 0,
        speed_override: cur.speed_override ?? null,
        variant: cur.variant ?? null,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      const detail = (data.stderr || data.stdout || '').slice(-400);
      console.error('[patch-shot]', data);
      toast(`Не удалось применить ${shotKey}: ${data.message || '???'}`, 'error');
      if (detail) alert(`Патч ${shotKey} не прошёл:\n\n${data.message || ''}\n\n${detail}`);
    } else {
      console.log('[patch-shot]', data.stdout);
      btn.classList.add('is-done');
      setTimeout(() => btn.classList.remove('is-done'), 1500);
      toast(`Сцена ${shotKey} обновлена в CapCut (без пересборки).`, 'success');
    }
  } catch (e) {
    toast(`Ошибка сети при патче ${shotKey}: ${e.message}`, 'error');
  } finally {
    btn.dataset.busy = '0';
    btn.classList.remove('is-busy');
  }
}

async function savePlanState(summary, state) {
  try {
    const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shots: state.shots }),
    });
    const data = await res.json();
    if (!data.ok) {
      toast('Не удалось сохранить план: ' + (data.message || '???'), 'error');
      return false;
    }
    return true;
  } catch (e) {
    toast('Ошибка сети при сохранении плана: ' + e.message, 'error');
    return false;
  }
}


// ═══════════════════════════════════════════════════════════════════
// РЕДАКТОР ПЕРЕХОДОВ · шаг 2 · макет «Партитура стыков»
// ═══════════════════════════════════════════════════════════════════
// Открывается из cv-step (шаг 2, action="edit-plan"). Грузит реальные
// переходы из живого CapCut-драфта (/transitions) + каталог канон-
// переходов, рисует ряды-стыки с дропдауном перехода и слайдером
// длительности. «Сохранить» пишет план прямо в draft_content.json
// (с бэкапом) и расставляет канон-SFX. CapCut должен быть закрыт.

const TX_FAMILY_LABELS = {
  cut: 'Без перехода', zoom: 'Зум', directional: 'Направленные',
  swish: 'Взмах', paper: 'Бумага', texture: 'Фактурные',
};
const TX_FAMILY_ORDER = ['cut', 'zoom', 'directional', 'swish', 'paper', 'texture'];

function txSfxBadge(sfx) {
  if (sfx === 'whoosh') return { text: 'WHOOSH · 0.70', cls: 'tx-sfx-local' };
  if (sfx === 'crumpled') return { text: 'crumpled · 1.00', cls: 'tx-sfx-local' };
  if (sfx === 'swoosh') return { text: 'Swoosh · вручную', cls: 'tx-sfx-manual' };
  return { text: '—', cls: 'tx-sfx-none' };
}

async function openTransitionEditor(summary) {
  document.getElementById('trans-editor-overlay')?.remove();

  const overlay = document.createElement('div');
  overlay.id = 'trans-editor-overlay';
  overlay.className = 'pe-overlay';
  overlay.innerHTML = `
    <div class="pe-shell">
      <div class="pe-loading">
        <div class="pe-spinner"></div>
        <div>Читаю переходы из CapCut-драфта…</div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeTransitionEditor(); });
  const onEsc = (e) => { if (e.key === 'Escape') closeTransitionEditor(); };
  document.addEventListener('keydown', onEsc);
  overlay._escHandler = onEsc;

  let data;
  try {
    data = await fetchJSON(`/api/montage/${encodeURIComponent(summary.name)}/transitions`);
  } catch (e) {
    overlay.querySelector('.pe-shell').innerHTML = `<div class="pe-error">Ошибка сети: ${escapeHtml(e.message)}</div>`;
    return;
  }
  if (!data.ok) {
    overlay.querySelector('.pe-shell').innerHTML = `<div class="pe-error">${escapeHtml(data.message || 'Не удалось загрузить переходы')}</div>`;
    return;
  }
  if (!data.ready) {
    overlay.querySelector('.pe-shell').innerHTML = `
      <div class="pe-error" style="color:var(--text-dim)">
        Скелет ещё не собран — запусти шаг 1, потом возвращайся за переходами.
      </div>`;
    return;
  }

  const catalog = data.catalog || [];
  const catById = {};
  catalog.forEach(c => { if (c.effect_id) catById[c.effect_id] = c; });

  // state — массив стыков; каждый хранит текущий + исходный выбор (для reset).
  const state = data.transitions.map((t, i) => ({
    index: i,
    from: t.from, to: t.to,
    effect_id: t.effect_id,
    duration: t.duration ?? (t.effect_id && catById[t.effect_id] ? catById[t.effect_id].default_dur_us / 1e6 : null),
    orig_effect_id: t.effect_id,
    orig_duration: t.duration,
  }));

  overlay.querySelector('.pe-shell').innerHTML = renderTransitionEditorShell(summary, state, catalog);
  wireTransitionEditor(overlay, summary, state, catById);
}

function closeTransitionEditor() {
  const ov = document.getElementById('trans-editor-overlay');
  if (!ov) return;
  if (ov._escHandler) document.removeEventListener('keydown', ov._escHandler);
  ov.classList.add('pe-out');
  setTimeout(() => ov.remove(), 160);
}

function renderTxSelect(catalog, selectedEid) {
  const byFam = {};
  catalog.forEach(c => { (byFam[c.family] = byFam[c.family] || []).push(c); });
  const groups = TX_FAMILY_ORDER.filter(f => byFam[f]).map(fam => {
    if (fam === 'cut') {
      const c = byFam.cut[0];
      const sel = !selectedEid ? 'selected' : '';
      return `<option value="" ${sel}>${escapeHtml(c.name)}</option>`;
    }
    const opts = byFam[fam].map(c => {
      const sel = c.effect_id === selectedEid ? 'selected' : '';
      return `<option value="${c.effect_id}" ${sel}>${escapeHtml(c.name)}</option>`;
    }).join('');
    return `<optgroup label="${escapeHtml(TX_FAMILY_LABELS[fam])}">${opts}</optgroup>`;
  }).join('');
  return `<select class="tx-select" data-tx-select>${groups}</select>`;
}

function renderTransitionEditorShell(summary, state, catalog) {
  const total = state.length;
  const picked = state.filter(s => s.effect_id).length;
  const rows = state.map(s => renderTransitionRow(s, catalog)).join('');

  return `
    <header class="pe-head">
      <div class="pe-head-left">
        <div class="pe-bcrumb">сборка / pipeline / capcut / <em>редактор переходов</em></div>
        <h2>Редактор <i>переходов</i> · <span class="pe-step">шаг 2</span>
          <small>${escapeHtml(summary.display_name)} · ${total} стыков · CapCut закроется и откроется сам</small>
        </h2>
      </div>
      <div class="pe-head-meta">
        <div><b class="pe-mint" data-tx-picked>${picked}</b><span>переходов</span></div>
        <div><b data-tx-cut>${total - picked}</b><span>cut</span></div>
        <div><b>${total}</b><span>стыков</span></div>
      </div>
      <button class="pe-close" title="Закрыть (Esc)">×</button>
    </header>

    <div class="pe-toolbar">
      <span class="pe-lbl">фильтр</span>
      <button class="pe-chip is-on" data-tx-filter="all">всё (${total})</button>
      <button class="pe-chip" data-tx-filter="picked">с переходом (<span data-tx-picked>${picked}</span>)</button>
      <button class="pe-chip" data-tx-filter="cut">cut (<span data-tx-cut>${total - picked}</span>)</button>
      <span class="pe-grow"></span>
      <button class="pe-ghost" data-tx-action="reset-all">⟲ вернуть как в драфте</button>
    </div>

    <div class="tx-grid-head">
      <span>стык</span>
      <span>переход</span>
      <span>длительность · 0.2 — 2.0 s</span>
      <span>sfx</span>
      <span style="text-align:center">⟳ ↺</span>
    </div>
    <div class="pe-rows" data-tx-rows>${rows}</div>

    <footer class="pe-footer">
      <span class="pe-summary"><b data-tx-edited>0</b> правок · запустит шаг 2 (переходы + SFX)</span>
      <span class="pe-grow"></span>
      <button class="pe-btn pe-btn-secondary" data-tx-action="cancel">Отменить</button>
      <button class="pe-btn pe-btn-primary" data-tx-action="save">Сохранить и запустить шаг 2</button>
    </footer>
  `;
}

function renderTransitionRow(s, catalog) {
  const cat = s.effect_id ? catalog.find(c => c.effect_id === s.effect_id) : null;
  const badge = txSfxBadge(cat ? cat.sfx : null);
  const isCut = !s.effect_id;
  const durVal = s.duration != null ? s.duration : 0.7;
  return `
    <div class="tx-row" data-tx-index="${s.index}">
      <span class="tx-sid"><b>${s.from}</b><i>→</i><b>${s.to}</b></span>
      <span class="tx-pick">${renderTxSelect(catalog, s.effect_id)}</span>
      <span class="pe-ctrl tx-dur">
        <input type="range" min="0.2" max="2.0" step="0.01" value="${durVal}" data-tx-dur ${isCut ? 'disabled' : ''}>
        <span class="pe-val ${isCut ? 'pe-auto' : 'pe-mint'}" data-tx-durval>${isCut ? '—' : durVal.toFixed(2) + ' s'}</span>
      </span>
      <span class="tx-sfx ${badge.cls}" data-tx-sfx>${escapeHtml(badge.text)}</span>
      <span class="tx-rowactions">
        <button class="pe-apply" data-tx-apply title="Применить только этот стык к CapCut-драфту (без полной записи)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9"/><path d="m3 3 9 9"/></svg>
        </button>
        <button class="pe-reset-row" data-tx-reset title="Вернуть как в драфте">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 2v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L3 8"/></svg>
        </button>
      </span>
    </div>`;
}

function wireTransitionEditor(overlay, summary, state, catById) {
  const recount = () => {
    const picked = state.filter(s => s.effect_id).length;
    const edited = state.filter(s =>
      s.effect_id !== s.orig_effect_id ||
      (s.effect_id && Math.abs((s.duration || 0) - (s.orig_duration || 0)) > 0.005)
    ).length;
    overlay.querySelectorAll('[data-tx-picked]').forEach(el => { el.textContent = picked; });
    overlay.querySelectorAll('[data-tx-cut]').forEach(el => { el.textContent = state.length - picked; });
    const ed = overlay.querySelector('[data-tx-edited]');
    if (ed) ed.textContent = edited;
  };
  overlay._txRecount = recount;

  const syncRow = (row, s) => {
    const cat = s.effect_id ? catById[s.effect_id] : null;
    const badge = txSfxBadge(cat ? cat.sfx : null);
    const isCut = !s.effect_id;
    const durInput = row.querySelector('[data-tx-dur]');
    const durVal = row.querySelector('[data-tx-durval]');
    const sfxEl = row.querySelector('[data-tx-sfx]');
    durInput.disabled = isCut;
    if (isCut) {
      durVal.textContent = '—';
      durVal.classList.add('pe-auto'); durVal.classList.remove('pe-mint');
    } else {
      durInput.value = String(s.duration ?? 0.7);
      durVal.textContent = (s.duration ?? 0.7).toFixed(2) + ' s';
      durVal.classList.remove('pe-auto'); durVal.classList.add('pe-mint');
    }
    sfxEl.textContent = badge.text;
    sfxEl.className = `tx-sfx ${badge.cls}`;
    const editedRow = s.effect_id !== s.orig_effect_id ||
      (s.effect_id && Math.abs((s.duration || 0) - (s.orig_duration || 0)) > 0.005);
    row.classList.toggle('is-edited', !!editedRow);
  };

  overlay.querySelectorAll('.tx-row').forEach(row => {
    const idx = parseInt(row.dataset.txIndex, 10);
    const s = state[idx];
    const select = row.querySelector('[data-tx-select]');
    const durInput = row.querySelector('[data-tx-dur]');

    select.addEventListener('change', () => {
      const eid = select.value || null;
      s.effect_id = eid;
      if (eid) {
        // При выборе перехода — подставляем дефолтную длительность каталога.
        const cat = catById[eid];
        s.duration = cat ? +(cat.default_dur_us / 1e6).toFixed(2) : 0.7;
      }
      syncRow(row, s);
      recount();
    });

    durInput.addEventListener('input', () => {
      s.duration = parseFloat(durInput.value);
      const durVal = row.querySelector('[data-tx-durval]');
      durVal.textContent = s.duration.toFixed(2) + ' s';
      durVal.classList.remove('pe-auto'); durVal.classList.add('pe-mint');
      row.classList.add('is-edited');
      recount();
    });

    const applyBtn = row.querySelector('[data-tx-apply]');
    applyBtn.addEventListener('click', () => applyTransitionOne(summary, s, applyBtn));

    const resetBtn = row.querySelector('[data-tx-reset]');
    resetBtn.addEventListener('click', () => {
      s.effect_id = s.orig_effect_id;
      s.duration = s.orig_duration ?? (s.effect_id && catById[s.effect_id] ? +(catById[s.effect_id].default_dur_us / 1e6).toFixed(2) : null);
      select.value = s.effect_id || '';
      syncRow(row, s);
      recount();
    });
  });

  // Фильтр
  overlay.querySelectorAll('.pe-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      overlay.querySelectorAll('.pe-chip').forEach(c => c.classList.remove('is-on'));
      chip.classList.add('is-on');
      const f = chip.dataset.txFilter;
      overlay.querySelectorAll('.tx-row').forEach(row => {
        const s = state[parseInt(row.dataset.txIndex, 10)];
        let show = true;
        if (f === 'picked') show = !!s.effect_id;
        else if (f === 'cut') show = !s.effect_id;
        row.style.display = show ? '' : 'none';
      });
    });
  });

  // Вернуть всё как в драфте
  overlay.querySelector('[data-tx-action="reset-all"]').addEventListener('click', () => {
    overlay.querySelectorAll('.tx-row').forEach(row => {
      const s = state[parseInt(row.dataset.txIndex, 10)];
      s.effect_id = s.orig_effect_id;
      s.duration = s.orig_duration ?? (s.effect_id && catById[s.effect_id] ? +(catById[s.effect_id].default_dur_us / 1e6).toFixed(2) : null);
      row.querySelector('[data-tx-select]').value = s.effect_id || '';
      syncRow(row, s);
    });
    recount();
  });

  overlay.querySelector('.pe-close').addEventListener('click', closeTransitionEditor);
  overlay.querySelector('[data-tx-action="cancel"]').addEventListener('click', closeTransitionEditor);

  overlay.querySelector('[data-tx-action="save"]').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    if (btn.dataset.busy === '1') return;
    btn.dataset.busy = '1';
    btn.textContent = 'Шаг 2 идёт…';
    const plan = state.map(s => ({
      index: s.index,
      effect_id: s.effect_id,
      duration: s.effect_id ? s.duration : undefined,
    }));
    try {
      const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/transitions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transitions: plan }),
      });
      const data = await res.json();
      if (!data.ok) {
        toast(data.message || 'Не удалось сохранить переходы', res.status === 409 ? 'warn' : 'error');
        btn.dataset.busy = '0';
        btn.textContent = 'Сохранить и запустить шаг 2';
        return;
      }
      toast(`Шаг 2 готов: ${data.picked} переходов, ${data.total - data.picked} cut. Если CapCut был открыт — он перезапущен с проектом.`, 'success');
      closeTransitionEditor();
      loadConveyorTransitions(summary.name);
    } catch (err) {
      toast('Ошибка сети при сохранении: ' + err.message, 'error');
      btn.dataset.busy = '0';
      btn.textContent = 'Сохранить и запустить шаг 2';
    }
  });

  recount();
}

// Точечное применение одного стыка к живому CapCut-драфту (аналог
// applyPlanShot на шаге 1). Прочие стыки сохраняются как в драфте.
async function applyTransitionOne(summary, s, btn) {
  if (btn.dataset.busy === '1') return;
  btn.dataset.busy = '1';
  btn.classList.add('is-busy');
  try {
    const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/transitions/apply-one`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        index: s.index,
        effect_id: s.effect_id,
        duration: s.effect_id ? s.duration : undefined,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      toast(data.message || `Не удалось применить стык ${s.from}→${s.to}`,
            res.status === 409 ? 'warn' : 'error');
      return;
    }
    // Стык применён — он больше не «правка»: фиксируем как исходный.
    s.orig_effect_id = s.effect_id;
    s.orig_duration = s.effect_id ? s.duration : null;
    const row = btn.closest('.tx-row');
    if (row) row.classList.remove('is-edited');
    const ov = document.getElementById('trans-editor-overlay');
    if (ov && ov._txRecount) ov._txRecount();
    btn.classList.add('is-done');
    setTimeout(() => btn.classList.remove('is-done'), 1500);
    toast(`Стык ${s.from}→${s.to} применён в CapCut-драфте.`, 'success');
    loadConveyorTransitions(summary.name);
  } catch (err) {
    toast(`Ошибка сети при применении стыка ${s.from}→${s.to}: ${err.message}`, 'error');
  } finally {
    btn.dataset.busy = '0';
    btn.classList.remove('is-busy');
  }
}


// Запуск automation/conveyor/step_1_build.py из webapp.
//
// Blocking-вызов: бэкенд держит соединение пока скрипт работает (10-60 с
// без whisper, до 5+ минут с whisper-medium). На кнопке показываем
// спиннер и блокируем повторный клик; по завершении показываем toast и
// перерисовываем хаб монтажа, чтобы шаг 1 стал «готов».
async function runMontageStep1(summary, btn, opts = {}) {
  if (btn.dataset.busy === '1') return;
  btn.dataset.busy = '1';
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<svg class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="9" stroke-opacity="0.3"/><path d="M21 12a9 9 0 0 0-9-9"/></svg><span class="stack">Собираю скелет…<small>step_1_build.py</small></span>`;
  toast(`Шаг 1: запускаю build для «${summary.display_name}»…`);

  try {
    const res = await fetch(`/api/montage/${encodeURIComponent(summary.name)}/step/1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ karaoke: 'auto' }),
    });
    const data = await res.json();
    if (!data.ok) {
      const detail = (data.stderr || data.stdout || '').slice(-600);
      console.error('[step1] exit', data.exit_code, '\nstdout:', data.stdout, '\nstderr:', data.stderr);
      toast(`Шаг 1 упал (exit=${data.exit_code ?? '?'}). См. консоль.`, 'error');
      alert(`Шаг 1 не завершился:\n\n${data.message || ''}\n\nПоследние строки лога:\n${detail || '— пусто —'}`);
    } else {
      console.log('[step1] stdout:\n', data.stdout);
      toast(`Шаг 1 готов: «${data.project_name}» собран в CapCut.`);
      // Обновляем summaries, чтобы новый montage_step подтянулся, и
      // заново рисуем текущую конвейерную страницу — шаг 1 станет «готов».
      try {
        state.summaries = await fetchJSON('/api/montage/myths');
        renderConveyor(summary.name);
      } catch (e) {
        console.warn('Не удалось обновить конвейер после шага 1:', e);
      }
    }
  } catch (e) {
    console.error(e);
    toast(`Не удалось запустить шаг 1: ${e.message}`, 'error');
  } finally {
    btn.dataset.busy = '0';
    btn.disabled = false;
    btn.innerHTML = originalHTML;
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
    applyPublishResult(summary, result);
    // Если этот же миф открыт в ревью — синхронизируем bottombar
    if (state.scenario === scenario || state.scenario === result.name) {
      state.scenario = result.name;
      state.scenarioPublished = summary.published;
      state.scenarioPublishedAt = summary.published_at;
      refreshBottombarPublishBtn();
    }
    renderHubList();
    renderHubDetail();
    const moved = result.archived && result.moved && result.moved.length;
    toast(
      next
        ? (moved
            ? `«${summary.display_name}» — опубликован, перенесён в архив`
            : `«${summary.display_name}» — опубликован`)
        : `«${summary.display_name}» — отметка снята`
    );
  } catch (e) {
    toast('Не удалось переключить публикацию: ' + e.message, 'error');
  }
}

// Применяем ответ /publish к summary: флаг публикации, дата, новое имя
// после переноса в архив. Имя обновляем СОГЛАСОВАННО с hubSelectedName,
// чтобы клики дальше не промахивались.
function applyPublishResult(summary, result) {
  const oldName = summary.name;
  summary.published = !!result.published;
  summary.published_at = result.published_at;
  if (result.name && result.name !== oldName) {
    summary.name = result.name;
    summary.is_archived = !!result.archived;
    if (state.hubSelectedName === oldName) {
      state.hubSelectedName = result.name;
    }
    // hubSceneCache ключуется по `${mode}::${scenario}` — после переноса
    // ключи устаревают. Вычищаем, чтобы при следующем открытии ревью
    // фронт перечитал содержимое по новому имени.
    Object.keys(state.hubSceneCache || {}).forEach(k => {
      if (k.endsWith(`::${oldName}`)) delete state.hubSceneCache[k];
    });
  } else if (typeof result.archived === 'boolean') {
    summary.is_archived = result.archived;
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
  // Часть сериала: кнопка работает (ставит флаг published), но без
  // переноса в архив — discovery 2-уровневое, архив серий не поддержан.
  const series = isSeries(state.scenario);
  btn.disabled = false;
  btn.title = series
    ? 'Пометить часть сериала опубликованной (без переноса в архив)'
    : 'Пометить миф опубликованным — папка переедет в content/архив/';
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
    // Бэкенд при on=true мог перенести миф в архив — имя сценария
    // поменялось. Обновляем активный scenario, summary и URL-хэш.
    const summary = state.summaries.find(s => s.name === state.scenario);
    if (summary) applyPublishResult(summary, result);
    if (result.name && result.name !== state.scenario) {
      state.scenario = result.name;
      // Пересобираем hash текущей записи через writeHash — он сам делает
      // encodeURIComponent и НЕ создаёт новую history-запись (это та же
      // сцена под новым адресом). F5 на новом URL откроет переехавший миф.
      const parts = ['review', state.mode || 'voice', result.name];
      if (state.activeSceneBase) parts.push(state.activeSceneBase);
      writeHash(parts);
    }
    refreshBottombarPublishBtn();
    const moved = result.archived && result.moved && result.moved.length;
    toast(
      next
        ? (moved ? 'миф опубликован · перенесён в архив' : 'миф помечен опубликованным')
        : 'отметка снята'
    );
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
  // Для одиночных мифов имя = display_name. Для частей сериала id
  // содержит слеш («От Хаоса до Олимпа/часть_01_Хаос»), а в шапке
  // показываем красивое «От Хаоса до Олимпа — Ч.01 Хаос» из summary.
  const sum = (state.summaries || []).find(s => s.name === scenario);
  const titleText = sum && sum.display_name
    ? sum.display_name
    : scenario.replace(/_/g, ' ');
  scenarioTitle.textContent = titleText;
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
  // Путь к mp3 относительно voiceover/audio/. Передаём query-параметром,
  // потому что бэкенд-эндпоинт `/audio/<scenario>` ожидает `?path=<file>`.
  // Раньше путь был в URL-сегменте, но из-за scenario со слешем
  // («От Хаоса до Олимпа/часть_01_Хаос») werkzeug-роутинг ломался — два
  // <path:>-параметра подряд резолвились неоднозначно.
  const audioPath = variant.path || variant.filename;
  // Cache-buster: после перегенерации mp3 имя файла не меняется, но
  // контент другой — без query-параметра браузер отдаёт старую озвучку
  // из HTTP-кеша. size_kb меняется между разными генерациями, поэтому
  // служит стабильным хешем содержимого.
  const cacheKey = variant.size_kb != null ? `&v=${variant.size_kb}` : '';
  const audioUrl = `/audio/${encodeURIComponent(state.scenario)}?path=${encodeURIComponent(audioPath)}${cacheKey}`;
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
  // Картинки через query — иначе для частей сериала со слешем в scenario
  // werkzeug-роутинг ломается (два path-сегмента после <path:scenario>).
  const imgUrl = `/image/${encodeURIComponent(state.scenario)}?scene=${encodeURIComponent(scene.base)}&file=${encodeURIComponent(variant.filename)}`;
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
  // Файл через ?file= — иначе для частей сериала со слешем в scenario
  // werkzeug сломается на двух path-сегментах подряд.
  const sc = encodeURIComponent(state.scenario);
  return `/video/${sc}?file=${encodeURIComponent(filename)}&t=${Date.now()}`;
}

function videoThumbUrl(approvedPath) {
  const fname = extractApprovedBasename(approvedPath);
  if (!fname) return '';
  return `/video-thumb/${encodeURIComponent(state.scenario)}?file=${encodeURIComponent(fname)}`;
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

// ── CosyVoice speed (persisted UI setting) ────────────────────────────────
//
// Скорость синтеза CosyVoice 3 теперь редактируется из модалки регенерации
// (раньше была захардкожена 1.1). Храним в localStorage, читаем валидируя:
// если значение бьётся (NaN, вне диапазона) — откатываемся на дефолт 1.1.
const COSY_SPEED_KEY = 'cosyVoiceSpeed';
const COSY_SPEED_DEFAULT = 1.1;
const COSY_SPEED_MIN = 0.7;
const COSY_SPEED_MAX = 1.5;

function getCosySpeed() {
  const raw = localStorage.getItem(COSY_SPEED_KEY);
  if (raw === null) return COSY_SPEED_DEFAULT;
  const v = parseFloat(raw);
  if (!Number.isFinite(v)) return COSY_SPEED_DEFAULT;
  return Math.min(COSY_SPEED_MAX, Math.max(COSY_SPEED_MIN, v));
}

function setCosySpeed(value) {
  const num = parseFloat(value);
  if (!Number.isFinite(num)) return;
  const clamped = Math.min(COSY_SPEED_MAX, Math.max(COSY_SPEED_MIN, num));
  localStorage.setItem(COSY_SPEED_KEY, String(clamped));
}
// Inline oninput в bodyHtml модалки видит только глобальный scope.
window.setCosySpeed = setCosySpeed;

function speedControlHtml() {
  const v = getCosySpeed();
  return `
    <div class="mb-stat">
      <span class="mb-stat-label">Скорость</span>
      <input type="number"
             class="mb-speed-input"
             id="cosy-speed-input"
             min="${COSY_SPEED_MIN}"
             max="${COSY_SPEED_MAX}"
             step="0.05"
             value="${v.toFixed(2)}"
             oninput="window.setCosySpeed(this.value)" />
      <span class="mb-stat-num" style="flex:0 0 auto">×</span>
    </div>
  `;
}

// ── CosyVoice variants count (persisted UI setting) ───────────────────────
//
// Раньше число вариантов на предложение было захардкожено (10). Теперь
// пользователь может выбрать в модалке «Озвучить весь миф?». Меньше
// вариантов = быстрее, но меньше выбора при ревью.
const COSY_VARIANTS_KEY = 'cosyVoiceVariants';
const COSY_VARIANTS_DEFAULT = 10;
const COSY_VARIANTS_MIN = 1;
const COSY_VARIANTS_MAX = 20;

function getCosyVariants() {
  const raw = localStorage.getItem(COSY_VARIANTS_KEY);
  if (raw === null) return COSY_VARIANTS_DEFAULT;
  const v = parseInt(raw, 10);
  if (!Number.isFinite(v) || v < 1) return COSY_VARIANTS_DEFAULT;
  return Math.min(COSY_VARIANTS_MAX, Math.max(COSY_VARIANTS_MIN, v));
}

function setCosyVariants(value) {
  const num = parseInt(value, 10);
  if (!Number.isFinite(num)) return;
  const clamped = Math.min(COSY_VARIANTS_MAX, Math.max(COSY_VARIANTS_MIN, num));
  localStorage.setItem(COSY_VARIANTS_KEY, String(clamped));
}
window.setCosyVariants = setCosyVariants;

function variantsControlHtml() {
  const v = getCosyVariants();
  return `
    <div class="mb-stat">
      <span class="mb-stat-label">Вариантов на предложение</span>
      <input type="number"
             class="mb-speed-input"
             id="cosy-variants-input"
             min="${COSY_VARIANTS_MIN}"
             max="${COSY_VARIANTS_MAX}"
             step="1"
             value="${v}"
             oninput="window.setCosyVariants(this.value)" />
    </div>
  `;
}

// ── CosyVoice voice selector (persisted UI setting) ──────────────────────
//
// Голос клонируется из assets/TTS/<voice>/{TTS.mp3,TTS.txt}. На фронте
// — короткий список с человеческими лейблами; в backend летит ASCII-id.
// Если в /api/cosyvoice-voices появится новый — достаточно добавить запись
// в COSY_VOICES здесь и в COSY_VOICES в webapp/app.py.
const COSY_VOICES = [
  { id: 'max',     label: 'Макс Энергичный' },
  { id: 'burunov', label: 'Сергей Бурунов'   },
];
const COSY_VOICE_KEY = 'cosyVoice';
const COSY_VOICE_DEFAULT = 'max';

function getCosyVoice() {
  const raw = localStorage.getItem(COSY_VOICE_KEY);
  if (raw && COSY_VOICES.some(v => v.id === raw)) return raw;
  return COSY_VOICE_DEFAULT;
}

function setCosyVoice(value) {
  if (!COSY_VOICES.some(v => v.id === value)) return;
  localStorage.setItem(COSY_VOICE_KEY, value);
}
window.setCosyVoice = setCosyVoice;

function cosyVoiceLabel(id) {
  const v = COSY_VOICES.find(x => x.id === id);
  return v ? v.label : id;
}

function voiceControlHtml() {
  const cur = getCosyVoice();
  const options = COSY_VOICES.map(v =>
    `<option value="${v.id}" ${v.id === cur ? 'selected' : ''}>${v.label}</option>`
  ).join('');
  return `
    <div class="mb-stat">
      <span class="mb-stat-label">Голос</span>
      <select id="cosy-voice-input"
              onchange="window.setCosyVoice(this.value)"
              style="
                background: var(--bg-panel);
                color: var(--text);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 4px 8px;
                font-family: var(--font-sans);
                font-size: 0.88rem;
              ">${options}</select>
    </div>
  `;
}

async function onRegenerate(base) {
  const isImage = state.mode === 'image';

  // Voice-режим: CosyVoice3 zero-shot c клонированием голоса.
  // Параметры: variants/speed/voice редактируются в модалке (UI-input в
  // localStorage), prompt-wav/txt подбирается backend'ом по voice-id из
  // assets/TTS/<voice>/{TTS.mp3,TTS.txt}.
  const cosyParams = {
    model: 'Fun-CosyVoice3-0.5B',
  };

  const cosyBody = `
    Сцена <b>${escapeHtml(base)}</b> будет заново озвучена моделью
    <b>${cosyParams.model}</b>.
    <div class="mb-stats" style="margin-top:12px">
      <div class="mb-stat"><span class="mb-stat-label">Модель</span><span class="mb-stat-num">CosyVoice3</span></div>
      ${voiceControlHtml()}
      ${variantsControlHtml()}
      ${speedControlHtml()}
    </div>
    <div class="mb-note" style="margin-top:10px">
      Клонирование голоса из <code>assets/TTS/&lt;голос&gt;/TTS.mp3</code>.
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
    // Скорость + кол-во вариантов + голос берём из localStorage в момент клика
    // по «Запустить» — модалка успела сохранить пользовательский ввод через
    // oninput/onchange.
    const chosenSpeed = isImage ? null : getCosySpeed();
    const chosenVariants = isImage ? null : getCosyVariants();
    const chosenVoice = isImage ? null : getCosyVoice();
    const body = isImage
      ? { base }
      : { base, speed: chosenSpeed, variants: chosenVariants, voice: chosenVoice };
    const res = await postJSON(api().regen(state.scenario), body);

    // В voice-режиме выводим параметры озвучки уведомлением.
    if (!isImage) {
      const parts = [
        `Модель: ${res.model || cosyParams.model}`,
        `Голос: ${res.voice_label || cosyVoiceLabel(chosenVoice)}`,
        `Вариантов: ${res.variants ?? chosenVariants}`,
        `Скорость: ${res.speed ?? chosenSpeed}`,
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
        requested: res.variants ?? chosenVariants,
        model: res.model || cosyParams.model,
        speed: res.speed ?? chosenSpeed,
        voiceLabel: res.voice_label || cosyVoiceLabel(chosenVoice),
        promptWav: res.prompt_wav || `assets/TTS/${cosyVoiceLabel(chosenVoice)}/TTS.mp3`,
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
  // Геттеры: при resume-е после перезагрузки страницы показываем актуальные
  // значения из localStorage, а не давно зашитые константы.
  get speed() { return getCosySpeed(); },
  get voice() { return getCosyVoice(); },
  get voiceLabel() { return cosyVoiceLabel(getCosyVoice()); },
  get promptWav() { return `assets/TTS/<${cosyVoiceLabel(getCosyVoice())}>/TTS.mp3`; },
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
  // variants — динамический геттер, читается из localStorage через
  // getCosyVariants() (UI-input в модалке). Раньше было статичное 10.
  get variants() { return getCosyVariants(); },
  get speed() { return getCosySpeed(); },
  // promptWav убран: голос выбирается в модалке (см. COSY_VOICES), и
  // backend сам подбирает assets/TTS/<voice>/{TTS.mp3,TTS.txt}.
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
      Запустим CosyVoice 3 на <b>${queue.length}</b> ${plural(queue.length, 'предложение', 'предложения', 'предложений')}
      одним прогоном — модель грузится <b>один раз</b> на весь батч.
      <div class="mb-stats" style="margin-top:12px">
        <div class="mb-stat"><span class="mb-stat-label">Модель</span><span class="mb-stat-num">${BATCH_META.model}</span></div>
        ${voiceControlHtml()}
        ${variantsControlHtml()}
        ${speedControlHtml()}
      </div>
      <div class="mb-note" style="margin-top:10px">
        Клон из <code>assets/TTS/&lt;голос&gt;/TTS.mp3</code>.
        Оценочное время — около <b>${Math.ceil(queue.length * 3 * getCosyVariants() / 60)}</b> мин (без повторных прогревов; ~3 сек на вариант).
        Во время работы можно открывать любую уже готовую сцену и ревьюить.
      </div>
    `,
    confirmText: 'Запустить',
  });
  if (!ok) return;

  // Фиксируем сценарий и параметры на момент клика — даже если пользователь
  // уйдёт смотреть другой проект, поллинг этого не заметит.
  const batchScenario = state.scenario;
  const speed = getCosySpeed();
  const variants = getCosyVariants();
  const voice = getCosyVoice();

  state.cosyBatch = {
    active: true,
    scenario: batchScenario,
    queue,                                   // оставляем для совместимости с UI
    currentBase: null,
    total: queue.length,
    completed: 0,
    produced: 0,
    requested: variants,
    startedAt: Date.now(),
    pollTimer: null,
    cancelRequested: false,
    error: null,
    // Сцены, которые мы уже подтянули через refreshSceneVariants, чтобы
    // не дёргать /api/scenes на каждый poll.
    refreshedBases: new Set(),
    pid: null,
  };
  renderSidebarAction();

  // Один POST на весь батч — runner внутри обходит все сцены без перезагрузки модели.
  try {
    const res = await postJSON(api().cosyBatchStart(batchScenario), {
      bases: queue,
      speed,
      variants,
      voice,
    });
    state.cosyBatch.pid = res.pid;
    state.cosyBatch.requested = res.variants ?? variants;
    toast(
      `CosyVoice batch · ${cosyVoiceLabel(voice)} · ${queue.length} сцен · ` +
      `скорость ${res.speed ?? speed} · PID ${res.pid}`,
      'success',
    );
  } catch (e) {
    state.cosyBatch.active = false;
    state.cosyBatch.error = e.message || 'не удалось запустить runner';
    toast(`Ошибка запуска batch: ${state.cosyBatch.error}`, 'error');
    renderSidebarAction();
    renderSidebar();
    return;
  }

  pollCosyBatchStatus();
}

// Поллер общего статуса batch-прогона. Один runner, один субпроцесс — фронт
// просто читает _cosyvoice_batch.json через эндпоинт каждые 1.5 сек и
// обновляет UI: текущую сцену, счётчик готовых, пипсы внутри активной сцены,
// прогресс новоготовых сцен (refreshSceneVariants) и финальное состояние.
async function pollCosyBatchStatus() {
  if (!state.cosyBatch.active) return;
  const batchScenario = state.cosyBatch.scenario;

  if (state.cosyBatch.cancelRequested) {
    // Cancel в option A не убивает subprocess — runner доработает batch до конца.
    // Просто перестаём поллить и уведомляем пользователя.
    state.cosyBatch.active = false;
    state.cosyBatch.currentBase = null;
    toast('Поллинг остановлен (runner продолжит в фоне)', 'success');
    renderSidebarAction();
    renderSidebar();
    return;
  }

  let status;
  try {
    status = await fetchJSON(api().cosyBatchStatus(batchScenario));
  } catch (e) {
    // Сетевые сбои — повторим через 3 сек, не валим батч.
    state.cosyBatch.pollTimer = setTimeout(pollCosyBatchStatus, 3000);
    return;
  }

  // Если фронт ушёл с этого сценария — тихо продолжаем поллить, чтобы по
  // возвращении пользователь увидел актуальное состояние; UI-обновления
  // ниже все ограничены state.scenario.
  const sameScenario = state.scenario === batchScenario;

  // Обновляем агрегаты в state.cosyBatch.
  state.cosyBatch.completed = status.completed_count || 0;
  state.cosyBatch.currentBase = status.current_base || null;
  state.cosyBatch.produced = status.current_produced || 0;
  state.cosyBatch.requested = status.variants || state.cosyBatch.requested;
  state.cosyBatch.total = status.total || state.cosyBatch.total;

  // Пипсы для активной сцены (если она в текущем сценарии).
  if (sameScenario && status.current_base) {
    updateSidebarPips(status.current_base, state.cosyBatch.produced, state.cosyBatch.requested);
  }

  // Подтягиваем варианты для каждой новоготовой сцены ровно один раз.
  if (sameScenario && Array.isArray(status.completed_bases)) {
    for (const base of status.completed_bases) {
      if (!state.cosyBatch.refreshedBases.has(base)) {
        state.cosyBatch.refreshedBases.add(base);
        // fire-and-forget: сцена обновится на следующем рендере,
        // нам не важен порядок завершения refresh-ей.
        refreshSceneVariants(batchScenario, base);
      }
    }
  }

  renderSidebarAction();

  // Жёсткие ошибки (model load fail, отсутствующие зависимости) — runner
  // пишет error в статус-файл и/или backend выставляет error_hint, и
  // active=false без done=true. Останавливаемся.
  const fatalError = status.error_hint && !status.active && !status.done;
  if (fatalError) {
    state.cosyBatch.active = false;
    state.cosyBatch.error = status.error_hint;
    toast(`Batch упал: ${status.error_hint}`, 'error');
    renderSidebarAction();
    renderSidebar();
    return;
  }

  if (status.done) {
    state.cosyBatch.active = false;
    state.cosyBatch.currentBase = null;
    const failed = (status.failed || []).length;
    if (failed > 0) {
      toast(
        `Готово · ${status.completed_count}/${status.total} (${failed} с ошибкой)`,
        'error',
      );
    } else {
      toast(`Озвучка готова · ${status.completed_count}/${status.total}`, 'success');
    }
    renderSidebarAction();
    if (sameScenario) {
      // Полный reload — подхватит финальный статус всех сцен и снимет
      // оранжевый regen-маркер с одобренных.
      await loadScenario(state.scenario, state.activeSceneBase);
    }
    return;
  }

  state.cosyBatch.pollTimer = setTimeout(pollCosyBatchStatus, 1500);
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
    meta.voiceLabel ? `голос ${meta.voiceLabel}` : null,
    `скорость ${meta.speed}`,
    `prompt ${meta.promptWav}`,
  ].filter(Boolean).join(' · ');
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
