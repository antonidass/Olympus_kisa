"""
CosyVoice3 HTTP-сервер — долгоживущий процесс, держит модель Fun-CosyVoice3-0.5B
в памяти и обслуживает HTTP-запросы webapp'а.

В отличие от `cosyvoice_runner.py` (одноразовый subprocess, грузит модель
~30 сек при каждом запуске), сервер грузит модель ОДИН раз при старте и
дальше обрабатывает задачи мгновенно. Архитектура:

  - Flask на 5001
  - Воркер-поток держит модель и крутит очередь задач (один GPU = одна задача
    в работе одновременно, остальные ждут)
  - Все задачи и история — в памяти (JobStore с лимитом на историю)
  - Файлы mp3 кладутся туда же, где их сейчас ждёт webapp:
    `content/<scenario>/voiceover/audio/review_sentences/<base>/<base>_vN.mp3`

Запускается отдельно от webapp:
    python automation/cosyvoice_server.py [--port 5001] [--host 127.0.0.1]

Webapp при загрузке стартовой страницы проверяет /health на 5001 и показывает
кнопку «Запустить CosyVoice-сервер», если он не отвечает.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Сбрасываем werkzeug-переменные ДО любых импортов flask/werkzeug.
# Если cosy-server спавнится из родительского Flask-процесса (наш webapp на 5000),
# werkzeug мог установить WERKZEUG_SERVER_FD / WERKZEUG_RUN_MAIN — и тогда
# наш дочерний flask пытается унаследовать сокет родителя через `socket.fromfd()`,
# что на Windows падает с `WinError 10038 — не сокет`. Чистим до import flask.
os.environ.pop("WERKZEUG_SERVER_FD", None)
os.environ.pop("WERKZEUG_RUN_MAIN", None)

# Принудительный line-buffering для stdout/stderr — чтобы при detached-режиме
# (логи перенаправлены в файл, нет TTY) print'ы сбрасывались на КАЖДОЙ строке,
# а не блоками по 4-8 КБ. Без этого пользователь смотрит в лог и думает что
# сервер «завис» на середине загрузки модели, хотя на самом деле он работает.
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    sys.stderr.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

# Этот модуль импортирует cosyvoice_runner (там реально живут load_model /
# generate_variants / _shatter_determinism). Чтобы не дублировать ~500 строк.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "automation"))

import cosyvoice_runner as cvr  # noqa: E402

try:
    from flask import Flask, jsonify, request, abort  # noqa: E402
except ImportError:  # pragma: no cover — bat-скрипт ставит flask автоматически
    print(
        "[cosy-server] ❌ Flask не установлен в этом интерпретаторе.\n"
        "  Выполни: pip install flask\n"
        f"  Текущий python: {sys.executable}",
        flush=True,
    )
    raise


CONTENT_DIR = REPO_ROOT / "content"
DEFAULT_PROMPT_WAV = cvr.DEFAULT_PROMPT_WAV
DEFAULT_PROMPT_TXT = cvr.DEFAULT_PROMPT_TXT
DEFAULT_VARIANTS = cvr.DEFAULT_VARIANTS
DEFAULT_SPEED = cvr.DEFAULT_SPEED

# Максимум задач, которые держим в истории (active + finished). Старые
# выкидываются — UI всё равно их не показывает.
HISTORY_LIMIT = 50


# ─── Job model ─────────────────────────────────────────────────────────────


@dataclass
class JobItem:
    """Одна сцена в batch-задаче (или единственная — в single)."""
    base: str
    text: str
    status: str = "queued"  # queued|running|done|failed|cancelled
    current_variant: int = 0
    files: list[str] = field(default_factory=list)
    error: str | None = None
    elapsed_sec: float = 0.0


@dataclass
class Job:
    id: str
    type: str  # "single" | "batch"
    scenario: str
    variants: int
    speed: float
    prompt_wav: str
    prompt_text: str
    items: list[JobItem]
    status: str = "queued"  # queued|running|done|failed|cancelled
    progress: dict = field(default_factory=dict)
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    started_at: str | None = None
    finished_at: str | None = None
    cancel_requested: bool = False

    def to_dict(self) -> dict[str, Any]:
        items_total = len(self.items)
        items_done = sum(1 for it in self.items if it.status == "done")
        items_failed = sum(1 for it in self.items if it.status == "failed")
        current_item = next(
            (i for i, it in enumerate(self.items) if it.status == "running"),
            None,
        )
        return {
            "id": self.id,
            "type": self.type,
            "scenario": self.scenario,
            "variants": self.variants,
            "speed": self.speed,
            "prompt_wav": self.prompt_wav,
            "prompt_text_preview": self.prompt_text[:120],
            "status": self.status,
            "progress": {
                **self.progress,
                "items_total": items_total,
                "items_done": items_done,
                "items_failed": items_failed,
                "current_item": current_item,
            },
            "items": [
                {
                    "base": it.base,
                    "text_preview": it.text[:120],
                    "status": it.status,
                    "current_variant": it.current_variant,
                    "files": it.files,
                    "error": it.error,
                    "elapsed_sec": round(it.elapsed_sec, 1),
                }
                for it in self.items
            ],
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cancel_requested": self.cancel_requested,
        }


# ─── JobStore: всё в памяти под одним лок'ом ───────────────────────────────


class JobStore:
    def __init__(self):
        self._lock = threading.Lock()
        # OrderedDict-подобная штука: храним все, history_limit — общий лимит.
        self._jobs: dict[str, Job] = {}
        # FIFO-очередь job_id для воркера
        self._queue: deque[str] = deque()
        # Уведомление воркеру о новом job (без активного polling).
        self._has_work = threading.Event()

    def add(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job
            self._queue.append(job.id)
            # Тримминг истории: оставляем последние HISTORY_LIMIT. Активные
            # и в очереди не выкидываем.
            terminal = [
                jid for jid, j in self._jobs.items()
                if j.status in ("done", "failed", "cancelled")
            ]
            if len(terminal) > HISTORY_LIMIT:
                # Сортируем по finished_at и выкидываем самые старые.
                terminal.sort(
                    key=lambda jid: self._jobs[jid].finished_at or self._jobs[jid].created_at
                )
                excess = len(terminal) - HISTORY_LIMIT
                for jid in terminal[:excess]:
                    self._jobs.pop(jid, None)
        self._has_work.set()

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_all(self, scenario: str | None = None, limit: int = 50) -> list[Job]:
        with self._lock:
            jobs = list(self._jobs.values())
        if scenario:
            jobs = [j for j in jobs if j.scenario == scenario]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def pop_next(self, timeout: float = 1.0) -> Job | None:
        """Берёт следующую queued-задачу. Блокирует до прихода новой или таймаута."""
        if not self._has_work.is_set():
            self._has_work.wait(timeout=timeout)
        with self._lock:
            while self._queue:
                jid = self._queue.popleft()
                job = self._jobs.get(jid)
                if job and job.status == "queued" and not job.cancel_requested:
                    return job
                # Скип отменённых/удалённых.
            if not self._queue:
                self._has_work.clear()
        return None

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status in ("done", "failed", "cancelled"):
                return False
            job.cancel_requested = True
            if job.status == "queued":
                # Можно сразу пометить — воркер до неё ещё не добрался.
                job.status = "cancelled"
                job.finished_at = datetime.now().isoformat(timespec="seconds")
            return True

    def delete(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status == "running":
                # Активную не удаляем — это безопаснее.
                return False
            self._jobs.pop(job_id, None)
            return True

    def scenario_active(self, scenario: str) -> dict[str, str]:
        """{base: job_id} для всех queued/running задач в этом сценарии."""
        out: dict[str, str] = {}
        with self._lock:
            for jid, job in self._jobs.items():
                if job.scenario != scenario:
                    continue
                if job.status not in ("queued", "running"):
                    continue
                for it in job.items:
                    if it.status in ("queued", "running"):
                        out[it.base] = jid
        return out


# ─── ModelWorker: один поток, держит модель, крутит очередь ────────────────


class ModelWorker(threading.Thread):
    daemon = True

    def __init__(self, store: JobStore, prompt_wav: Path, prompt_text: Path):
        super().__init__(name="cosyvoice-worker")
        self.store = store
        self.prompt_wav = prompt_wav
        self.prompt_text_file = prompt_text
        self._model = None
        self._set_seed = None
        self._model_loaded = threading.Event()
        self._model_load_error: str | None = None
        self._stop = threading.Event()

    def is_model_loaded(self) -> bool:
        return self._model_loaded.is_set()

    def get_model_error(self) -> str | None:
        return self._model_load_error

    def stop(self) -> None:
        self._stop.set()
        # Будим воркер из ожидания очереди.
        self.store._has_work.set()

    def run(self) -> None:
        # ── 1. Прогрев модели ──────────────────────────────────────────
        try:
            print("[cosy-worker] загружаю модель…", flush=True)
            t0 = time.time()
            self._model, self._set_seed = cvr.load_cosyvoice_model()
            cvr._shatter_determinism(self._model)
            print(
                f"[cosy-worker] модель готова за {time.time() - t0:.1f}s, "
                f"sr={self._model.sample_rate}",
                flush=True,
            )
            self._model_loaded.set()
        except Exception as e:  # noqa: BLE001
            import traceback
            self._model_load_error = f"{type(e).__name__}: {e}"
            print(
                f"[cosy-worker] ❌ модель не загрузилась: {e}\n"
                f"{traceback.format_exc()}",
                flush=True,
            )
            # Не выходим — пусть сервер живёт, /health покажет ошибку,
            # пользователь увидит её в UI.
            return

        # ── 2. Чтение prompt-text ──────────────────────────────────────
        try:
            prompt_text = self.prompt_text_file.read_text(encoding="utf-8").strip()
        except Exception as e:  # noqa: BLE001
            print(f"[cosy-worker] не смог прочитать prompt-text: {e}", flush=True)
            prompt_text = ""

        # ── 3. Главный цикл: берём задачу и обрабатываем ───────────────
        while not self._stop.is_set():
            job = self.store.pop_next(timeout=2.0)
            if job is None:
                continue
            self._process_job(job, prompt_text)

    # ── 3.1. Обработка одной задачи ────────────────────────────────────

    def _process_job(self, job: Job, default_prompt_text: str) -> None:
        if job.cancel_requested:
            job.status = "cancelled"
            job.finished_at = datetime.now().isoformat(timespec="seconds")
            return

        job.status = "running"
        job.started_at = datetime.now().isoformat(timespec="seconds")
        t_start = time.time()
        print(
            f"[cosy-worker] job {job.id} type={job.type} "
            f"scenario={job.scenario!r} items={len(job.items)}",
            flush=True,
        )

        # Каждая Job может переопределить prompt-text — это для будущего,
        # когда добавим выбор голоса.
        prompt_text = job.prompt_text or default_prompt_text
        prompt_wav = Path(job.prompt_wav) if job.prompt_wav else self.prompt_wav

        any_failed = False
        for item in job.items:
            if job.cancel_requested:
                if item.status == "queued":
                    item.status = "cancelled"
                continue
            self._process_item(job, item, prompt_wav, prompt_text)
            if item.status == "failed":
                any_failed = True

        # Финальный статус job
        if job.cancel_requested:
            job.status = "cancelled"
        elif any_failed and not any(it.status == "done" for it in job.items):
            job.status = "failed"
            job.error = "Все элементы провалились"
        else:
            job.status = "done"
        job.finished_at = datetime.now().isoformat(timespec="seconds")
        job.progress["total_elapsed_sec"] = round(time.time() - t_start, 1)
        print(
            f"[cosy-worker] job {job.id} → {job.status} "
            f"за {time.time() - t_start:.1f}s",
            flush=True,
        )

    def _process_item(
        self,
        job: Job,
        item: JobItem,
        prompt_wav: Path,
        prompt_text: str,
    ) -> None:
        item.status = "running"
        t_item = time.time()

        def _progress_cb(produced: int) -> None:
            item.current_variant = produced

        try:
            report = cvr.generate_variants(
                scenario=job.scenario,
                base=item.base,
                text=item.text,
                variants=job.variants,
                speed=job.speed,
                prompt_wav=prompt_wav,
                prompt_text=prompt_text,
                model=self._model,
                set_seed_fn=self._set_seed,
                progress_cb=_progress_cb,
            )
            item.files = report.get("files", [])
            item.elapsed_sec = time.time() - t_item
            item.current_variant = len(item.files)
            if item.files:
                item.status = "done"
            else:
                item.status = "failed"
                item.error = "0 файлов сгенерировано"
        except Exception as e:  # noqa: BLE001
            import traceback
            item.status = "failed"
            item.error = f"{type(e).__name__}: {e}"
            item.elapsed_sec = time.time() - t_item
            print(
                f"[cosy-worker]   item {item.base} FAIL: {e}\n"
                f"{traceback.format_exc()}",
                flush=True,
            )


# ─── Flask app ─────────────────────────────────────────────────────────────


def _read_text_for_base(scenario: str, base: str) -> str:
    """voiceover/texts/<base>.txt — источник правды по тексту сцены."""
    txt = CONTENT_DIR / scenario / "voiceover" / "texts" / f"{base}.txt"
    if not txt.exists():
        raise FileNotFoundError(f"нет {txt}")
    text = txt.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"пустой файл: {txt}")
    return text


def _list_bases_from_texts(scenario: str) -> list[str]:
    """Все sentence_NNN.txt в порядке номера сцены."""
    texts_dir = CONTENT_DIR / scenario / "voiceover" / "texts"
    if not texts_dir.exists():
        return []

    def _scene_num(name: str) -> int:
        import re
        m = re.search(r"\d+", name)
        return int(m.group()) if m else 999

    out = []
    for txt in sorted(texts_dir.glob("*.txt"), key=lambda p: _scene_num(p.stem)):
        out.append(txt.stem)
    return out


def make_app(store: JobStore, worker: ModelWorker, server_started_at: float) -> Flask:
    app = Flask(__name__)

    # CORS для webapp (5000 → 5001). Любой webapp на localhost может звать.
    @app.after_request
    def _cors(response):
        origin = request.headers.get("Origin", "")
        if origin.startswith("http://127.0.0.1") or origin.startswith("http://localhost"):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return ("", 204)

    # ── /health ────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": worker.is_model_loaded(),
            "model_error": worker.get_model_error(),
            "uptime_sec": round(time.time() - server_started_at, 1),
            "jobs_total": len(store._jobs),
            "queue_len": len(store._queue),
        })

    # ── /model ─────────────────────────────────────────────────────────
    @app.route("/model")
    def model_info():
        return jsonify({
            "name": "Fun-CosyVoice3-0.5B",
            "prompt_wav": str(worker.prompt_wav),
            "prompt_text": str(worker.prompt_text_file),
            "default_variants": DEFAULT_VARIANTS,
            "default_speed": DEFAULT_SPEED,
            "loaded": worker.is_model_loaded(),
            "load_error": worker.get_model_error(),
        })

    # ── /jobs (POST: create, GET: list) ───────────────────────────────
    @app.route("/jobs", methods=["POST"])
    def create_job():
        data = request.get_json(force=True) or {}
        job_type = data.get("type", "single")
        scenario = data.get("scenario", "").strip()
        if not scenario:
            abort(400, "scenario обязателен")
        if not (CONTENT_DIR / scenario).exists():
            abort(404, f"Сценарий {scenario!r} не найден")

        variants = int(data.get("variants") or DEFAULT_VARIANTS)
        speed = float(data.get("speed") or DEFAULT_SPEED)
        prompt_wav = data.get("prompt_wav") or str(worker.prompt_wav)
        prompt_text = data.get("prompt_text", "")
        if not prompt_text and Path(prompt_wav).with_suffix(".txt").exists():
            prompt_text = Path(prompt_wav).with_suffix(".txt").read_text(encoding="utf-8").strip()

        # Соберём items
        items: list[JobItem] = []
        if job_type == "single":
            base = data.get("base")
            if not base:
                abort(400, "base обязателен для type=single")
            text = data.get("text") or ""
            if not text:
                try:
                    text = _read_text_for_base(scenario, base)
                except (FileNotFoundError, ValueError) as e:
                    abort(400, str(e))
            items.append(JobItem(base=base, text=text))
        elif job_type == "batch":
            bases = data.get("bases")
            if not bases:
                bases = _list_bases_from_texts(scenario)
            if not bases:
                abort(400, "bases пуст и в voiceover/texts/ ничего не найдено")
            for base in bases:
                try:
                    text = _read_text_for_base(scenario, base)
                except (FileNotFoundError, ValueError) as e:
                    abort(400, f"{base}: {e}")
                items.append(JobItem(base=base, text=text))
        else:
            abort(400, f"unknown type: {job_type!r}, ожидаем single|batch")

        job = Job(
            id=uuid.uuid4().hex[:8],
            type=job_type,
            scenario=scenario,
            variants=variants,
            speed=speed,
            prompt_wav=prompt_wav,
            prompt_text=prompt_text,
            items=items,
        )
        store.add(job)
        return jsonify({"ok": True, "job_id": job.id, **job.to_dict()})

    @app.route("/jobs", methods=["GET"])
    def list_jobs():
        scenario = request.args.get("scenario")
        limit = int(request.args.get("limit", "20"))
        jobs = store.list_all(scenario=scenario, limit=limit)
        return jsonify({"jobs": [j.to_dict() for j in jobs]})

    @app.route("/jobs/<job_id>")
    def get_job(job_id: str):
        job = store.get(job_id)
        if not job:
            abort(404)
        return jsonify(job.to_dict())

    @app.route("/jobs/<job_id>/cancel", methods=["POST"])
    def cancel_job(job_id: str):
        ok = store.cancel(job_id)
        if not ok:
            abort(404, "Не найдена или уже завершена")
        return jsonify({"ok": True, "job_id": job_id})

    @app.route("/jobs/<job_id>", methods=["DELETE"])
    def delete_job(job_id: str):
        ok = store.delete(job_id)
        if not ok:
            abort(409, "Активную задачу удалить нельзя; сначала cancel")
        return jsonify({"ok": True})

    # ── /scenarios/<scenario>/active ──────────────────────────────────
    # Webapp-у нужно знать, какие сцены в работе для конкретного сценария —
    # чтобы рисовать индикаторы в сайдбаре.
    @app.route("/scenarios/<path:scenario>/active")
    def scenario_active(scenario: str):
        from urllib.parse import unquote
        scenario = unquote(scenario)
        return jsonify(store.scenario_active(scenario))

    return app


# ─── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CosyVoice3 HTTP-сервер")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--prompt-wav", type=Path, default=DEFAULT_PROMPT_WAV)
    ap.add_argument("--prompt-text", type=Path, default=DEFAULT_PROMPT_TXT)
    args = ap.parse_args(argv)

    print(f"[cosy-server] python = {sys.executable}", flush=True)
    print(f"[cosy-server] root   = {REPO_ROOT}", flush=True)
    print(f"[cosy-server] prompt = {args.prompt_wav}", flush=True)

    if not args.prompt_wav.exists():
        print(f"[cosy-server] ❌ prompt-wav не найден: {args.prompt_wav}", flush=True)
        return 2
    if not args.prompt_text.exists():
        print(f"[cosy-server] ❌ prompt-text не найден: {args.prompt_text}", flush=True)
        return 2

    server_started_at = time.time()
    store = JobStore()
    worker = ModelWorker(store, args.prompt_wav, args.prompt_text)
    worker.start()

    app = make_app(store, worker, server_started_at)

    print(f"[cosy-server] HTTP listening on http://{args.host}:{args.port}", flush=True)
    print(f"[cosy-server] модель грузится в фоне, /health покажет когда готова", flush=True)
    try:
        # threaded=True важен: иначе долгий /jobs POST (с большим payload)
        # заблокирует GET /health и UI решит, что сервер мёртв.
        app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("[cosy-server] остановка по Ctrl+C", flush=True)
    finally:
        worker.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
