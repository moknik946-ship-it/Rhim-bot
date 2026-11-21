# -*- coding: utf-8 -*-
"""مساعد Gemini لشات الفريق وتيليجرام باستخدام Gemini generateContent API."""
import asyncio
import os
import time
from collections import defaultdict, deque
from urllib.parse import quote
import httpx

API_KEY = os.environ.get("AI_API_KEY", "").strip()
MODEL = os.environ.get("AI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
MAX_REPLY_CHARS = max(80, min(350, int(os.environ.get("AI_MAX_REPLY_CHARS", "220"))))
COOLDOWN_SECONDS = max(3, int(os.environ.get("AI_COOLDOWN_SECONDS", "7")))
BASE = "https://generativelanguage.googleapis.com/v1beta"
_HISTORY = defaultdict(lambda: deque(maxlen=8))
_LAST = {}
_LOCKS = defaultdict(asyncio.Lock)
_FALLBACKS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
_SYSTEM = ("أنت مساعد ذكي داخل لعبة. أجب بلغة اللاعب، غالباً العربية العامية، باختصار ووضوح. "
           "لا تدّع أنك لاعب بشري ولا تنفذ أوامر داخل اللعبة؛ أجب عن الأسئلة فقط.")


def clear_history(sender_id):
    _HISTORY.pop(str(sender_id), None)


def _detail(response):
    try:
        err = response.json().get("error", {})
        msg = err.get("message") or response.text
        status = err.get("status")
        return (str(msg) + (f" [{status}]" if status else ""))[:240]
    except Exception:
        return (response.text or "رد غير معروف").replace("\n", " ")[:240]


async def _models(client):
    try:
        r = await client.get(BASE + "/models", headers={"x-goog-api-key": API_KEY})
        if r.is_error:
            return []
        found = []
        for item in r.json().get("models", []):
            name = str(item.get("name", ""))
            if name.startswith("models/") and "generateContent" in item.get("supportedGenerationMethods", []):
                found.append(name.split("/", 1)[1])
        ordered = [m for m in _FALLBACKS if m in found]
        ordered.extend(m for m in found if m not in ordered)
        if MODEL in found:
            ordered.insert(0, MODEL)
        return list(dict.fromkeys(ordered))[:10]
    except Exception:
        return []


async def ask(sender_id, question):
    if not API_KEY:
        return None, "ميزة AI غير مفعّلة. ضع مفتاح Gemini في AI_API_KEY أعلى main.py."
    question = " ".join((question or "").split())
    if not question:
        return None, "اكتب سؤالك بعد @ai. مثال: @ai كيف الحال؟"
    question = question[:700]
    sid = str(sender_id or "guest")
    async with _LOCKS[sid]:
        now = time.monotonic()
        wait = COOLDOWN_SECONDS - (now - _LAST.get(sid, 0))
        if wait > 0:
            return None, f"انتظر {int(wait) + 1} ثواني قبل سؤال جديد."
        _LAST[sid] = now
        history = _HISTORY[sid]
        contents = []
        for item in history:
            role = "model" if item["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": item["content"]}]})
        contents.append({"role": "user", "parts": [{"text": question}]})
        payload = {
            "system_instruction": {"parts": [{"text": _SYSTEM}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 180},
        }
        headers = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                models = await _models(client)
                if not models:
                    models = list(dict.fromkeys([MODEL] + _FALLBACKS))
                last_404 = None
                for model in models:
                    url = BASE + "/models/" + quote(model, safe="") + ":generateContent"
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code == 404:
                        last_404 = _detail(response)
                        continue
                    if response.status_code in (401, 403):
                        return None, "مفتاح Gemini غير صحيح أو Gemini API غير مفعّل للمشروع. " + _detail(response)
                    if response.status_code == 429:
                        return None, "تجاوزت حد الطلبات المتاح حالياً. انتظر قليلاً. " + _detail(response)
                    if response.is_error:
                        return None, f"Gemini رجّع خطأ ({response.status_code}). " + _detail(response)
                    data = response.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    answer = " ".join(str(x.get("text", "")) for x in parts if x.get("text"))
                    answer = " ".join(answer.split())
                    if not answer:
                        reason = data.get("promptFeedback", {}).get("blockReason", "")
                        return None, "Gemini لم يرجع نصاً" + (f" ({reason})" if reason else "")
                    history.append({"role": "user", "content": question})
                    history.append({"role": "assistant", "content": answer})
                    if len(answer) > MAX_REPLY_CHARS:
                        answer = answer[:MAX_REPLY_CHARS - 1].rsplit(" ", 1)[0] + "…"
                    return answer, None
                return None, "لم يعثر Gemini على نموذج متاح لهذا المفتاح. افتح Google AI Studio وتأكد من تفعيل Gemini API. آخر رد: " + str(last_404 or "404 Not Found")
        except httpx.TimeoutException:
            return None, "تأخر رد Gemini. جرّب بعد قليل."
        except httpx.RequestError:
            return None, "تعذر الاتصال بخوادم Gemini. تحقق من الإنترنت."
        except Exception as exc:
            return None, "حدث خطأ أثناء طلب AI: " + str(exc)[:160]
