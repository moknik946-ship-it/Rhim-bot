# -*- coding: utf-8 -*-
"""شكل رسائل تيليجرام: بطاقات هادية بخطوط وأيقونات (HTML)"""
import html
import logging
import os
import re
from telegram import ReplyKeyboardMarkup

BOT_NAME = os.environ.get("BOT_NAME", "Music Bot")
log = logging.getLogger("ui")


def esc(x):
    return html.escape(str(x), quote=False)


_LEAD = re.compile(r"^[^\w\u0600-\u06FF/]+")


def clean(text):
    """يشيل الإيموجي والرموز من أول نص الخطأ"""
    return _LEAD.sub("", str(text)).strip()


def card(icon, title, line=None, rows=(), note=None):
    """line: HTML جاهز (استخدم esc لأي نص من المستخدم)، rows: [(إيموجي, عنوان, قيمة)]"""
    out = [f"╭─ {icon} <b>{esc(title)}</b>"]
    if line:
        for ln in str(line).split("\n"):
            out.append(f"│ {ln}")
    if rows:
        out.append("│")
        for emo, label, val in rows:
            out.append(f"│ {emo} {esc(label)} ‹<code>{esc(val)}</code>›")
    out.append(f"╰─ <i>{esc(note)}</i>" if note else "╰─")
    return "\n".join(out)


def working(what, detail=None):
    rows = [("🎯", "الهدف", detail)] if detail else ()
    return card("⏳", "لحظة", esc(what) + " ...", rows)


def ok(title, line, rows=(), note=None):
    return card("✅", title, esc(line), rows, note)


def err(line, hint=None):
    return card("⚠️", "تنبيه", "🔸 " + esc(line), (), hint)


def usage(cmd, args, example):
    return card("📖", "طريقة الاستخدام", f"<code>{esc(cmd)} {esc(args)}</code>", [("💡", "مثال", example)])


def stopped(line):
    return card("⏹", "تم الإيقاف", esc(line))


def menu():
    return (
        f"╭─ 🎧 <b>{esc(BOT_NAME)}</b>\n"
        "│ موسيقى ورقص وفرق لفري فاير\n"
        "│\n"
        "├ 🎶 <b>الموسيقى</b>\n"
        "│   /music ‹كود_الفريق› [أغنية]\n"
        "│   /online  ·  /play  ·  /resume  ·  /stop\n"
        "│   /msgmusic ‹كود› ‹أغنية› | ‹رسالة›\n"
        "│\n"
        "├ 💃 <b>الرقص</b>\n"
        "│   /em ‹كود_الفريق›\n"
        "│   /dance ‹كود› ‹uid…› ‹رقم›\n"
        "│   /evo ‹كود› ‹uid…› ‹رقم›\n"
        "│\n"
        "├ 🛠 <b>الفرق</b>\n"
        "│   /team3  ·  /team5  ·  /team6  ‹uid›\n"
        "╰─ <i>داخل اللعبة اكتب !help في شات الفريق</i>"
    )


def admin_menu():
    return (
        "╭─ 👑 <b>لوحة الأدمن</b>\n"
        "│\n"
        "├ 💃 <b>رقص</b>\n"
        "│   /evos ‹كود_الفريق› ‹uid›  ← كل الرقصات بدون توقف\n"
        "│\n"
        "├ ⚙️ <b>التحكم</b>\n"
        "│   /on  ·  /off  ·  /status\n"
        "│   /stopall  ← يوقف كل البوتات ويرجعها متاحة\n"
        "│\n"
        "├ 👥 <b>المجموعات</b>\n"
        "│   /allow  ·  /disallow  ·  /kick  ·  /unban  ·  /groups\n"
        "│\n"
        "├ 🛡 <b>الأدمنية</b>\n"
        "│   /admins  ·  /addadmin  ·  /deladmin\n"
        "│\n"
        "├ 🚫 <b>إيقاف أمر</b>\n"
        "│   /stop ‹أمر›  ·  /enable ‹أمر›  ·  /enable  (القائمة)\n"
        "│\n"
        "├ 📢 <b>الاشتراك الإجباري</b>\n"
        "│   /addchannel ‹@قناة›  ·  /delchannel  ·  /channels\n"
        "│\n"
        "├ 👤 <b>الحسابات</b>\n"
        "│   /accounts  ·  /reload  ·  /addacc ‹uid:pass›\n"
        "╰─ <i>/stop يوقف أي رقص شغال</i>"
    )


def main_keyboard():
    """قائمة أزرار Telegram الرئيسية بدل الحاجة لحفظ أوامر القائمة."""
    return ReplyKeyboardMarkup(
        [["🤖 اسأل AI", "📖 المساعدة"], ["🎵 الموسيقى", "💃 الرقص"], ["👥 الفرق", "❌ إلغاء"]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="اختر زرّاً من القائمة…",
    )


async def reply(message, text, reply_markup=None):
    return await message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True,
                                    reply_markup=reply_markup)


async def edit(msg, text):
    try:
        return await msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:                       # مثل: الرسالة ما تغيرت
        log.debug("edit skipped: %s", e)
        return None
