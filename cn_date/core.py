"""中文自然语言日期时间解析（零依赖）。

支持：
- 相对日：今天 / 今晚 / 明天 / 后天 / 大后天
- 星期：周X / 星期X / 礼拜X（本周 / 下周 / 下下周）
- 偏移：N天后 / N周后 / N个月后 / N小时后 / N分钟后 / 半小时后
- 日号：本月X号 / 下月X号 / X号（本月）/ 月底
- 时刻：X点 / X点半 / X点X分 / X:XX，配合 凌晨 / 早上 / 上午 / 中午 / 下午 / 晚上 段词
- 组合：「明天下午3点」「下周一上午9点」「3天后晚上8点半」

默认值：日期缺省今天，时刻缺省 09:00；小时/分钟级偏移从 now 精确推移。
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

_DEFAULT_HOUR = 9

_WEEKDAYS = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}

_P_DAY_WORD = re.compile(r"(大后天|后天|明天|今晚|今天)")
_P_WEEKDAY = re.compile(r"(下下|下|本)?(?:周|星期|礼拜)([一二三四五六日天])")
_P_OFFSET = re.compile(r"(\d+|半|一两|两|俩|仨)\s*个?\s*(小时|分钟|分|天|日|周|星期|月)后")
_P_MONTH_DAY = re.compile(r"(下个?月|本月|这个月)?\s*(\d{1,2})\s*号")
_P_MERIDIEM = re.compile(r"(凌晨|早上|清晨|上午|中午|下午|午后|傍晚|晚上|夜里|深夜)")
_P_CLOCK = re.compile(r"(凌晨|早上|清晨|上午|中午|下午|午后|傍晚|晚上|夜里|深夜)?\s*"
                      r"(\d{1,2})\s*[点时:：]\s*(半|(\d{1,2})\s*分?)?")

_AFTER_OFFSET = {"凌晨": 0, "早上": 0, "清晨": 0, "上午": 0,
                 "中午": 12, "下午": 12, "午后": 12, "傍晚": 12,
                 "晚上": 12, "夜里": 12, "深夜": 12}


@dataclass
class ParseResult:
    dt: datetime
    has_date: bool   # 文本是否显式包含日期成分
    has_time: bool   # 文本是否显式包含时刻成分
    text: str        # 原文


def _next_monday(now: datetime) -> datetime:
    return now + timedelta(days=(7 - now.weekday()) % 7 or 7)


def _weekday_date(now: datetime, prefix: str, wd_name: str) -> datetime:
    target = _WEEKDAYS[wd_name]
    if prefix == "下":
        return _next_monday(now) + timedelta(days=target)
    if prefix == "下下":
        return _next_monday(now) + timedelta(days=7 + target)
    # 本周：未来（含今天）取本周，已过取下周
    ahead = (target - now.weekday()) % 7
    return now + timedelta(days=ahead)


def _add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.year * 12 + (dt.month - 1) + months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _apply_meridiem(hour: int, word: str | None) -> int:
    """按段词换算 24 小时制。"""
    if not word:
        return hour
    if word == "中午":
        return 12
    if word == "凌晨":
        # 凌晨12点 = 0 点；凌晨1~11 保持
        return 0 if hour == 12 else hour
    if word == "早上" and hour == 12:
        return 0  # 早上12点极少见，按 0 处理
    if _AFTER_OFFSET.get(word, 0) == 12 and hour < 12:
        return hour + 12
    return hour


def parse(text: str, now: datetime | None = None) -> ParseResult | None:
    """解析一句中文里的日期时间；无法解析返回 None。"""
    now = now or datetime.now()
    if not text or not text.strip():
        return None
    has_date = has_time = False
    date_part: datetime | None = None
    hour, minute = _DEFAULT_HOUR, 0

    # ---- 时刻 ----
    m = _P_CLOCK.search(text)
    if m:
        meridiem, hh, half, mm = m.groups()
        h = _apply_meridiem(int(hh), meridiem)
        minute = 30 if half == "半" else int(mm or 0)
        if not (0 <= h <= 23) or minute > 59 or int(hh) > 24:
            return None
        hour, has_time = h, True
        # 「今晚8点」这类：段词未出现但「今晚」已隐含晚间
        if meridiem is None and "今晚" in text and h < 12:
            hour = h + 12

    # ---- 相对偏移 ----
    m_off = _P_OFFSET.search(text)
    fixed_dt: datetime | None = None  # 小时/分钟级偏移直接给出精确时刻
    if m_off:
        num, unit = m_off.group(1), m_off.group(2)
        if unit in ("小时", "分钟", "分"):
            value = {"半": 0.5, "一两": 1, "两": 2, "俩": 2, "仨": 3}.get(num) or int(num)
            delta = timedelta(minutes=int(value * 60)) if unit == "小时" \
                else timedelta(minutes=value)
            fixed_dt = now + delta
            has_date = has_time = True
        elif unit == "月":
            value = {"两": 2, "俩": 2, "仨": 3, "一两": 1, "半": 1}.get(num) or int(num)
            date_part = _add_months(now, value).replace(hour=0, minute=0)
            has_date = True
        else:
            days = {"天": 1, "日": 1, "周": 7, "星期": 7}[unit]
            value = {"两": 2, "俩": 2, "仨": 3, "一两": 1, "半": 0}.get(num)
            if value is None:
                value = int(num)
            date_part = datetime(now.year, now.month, now.day) + timedelta(days=value * days)
            has_date = True

    # ---- 相对日 ----
    m = _P_DAY_WORD.search(text)
    if m:
        word = m.group(1)
        base = {"今天": 0, "今晚": 0, "明天": 1, "后天": 2, "大后天": 3}[word]
        date_part = datetime(now.year, now.month, now.day) + timedelta(days=base)
        has_date = True
        if word == "今晚" and not has_time:
            hour, minute, has_time = 20, 0, True

    # ---- 星期 ----
    if date_part is None:
        m = _P_WEEKDAY.search(text)
        if m:
            date_part = _weekday_date(now, m.group(1) or "", m.group(2))
            has_date = True

    # ---- 日号 / 月底 ----
    if date_part is None and "月底" in text:
        last = calendar.monthrange(now.year, now.month)[1]
        date_part = datetime(now.year, now.month, last)
        has_date = True
    if date_part is None:
        m = _P_MONTH_DAY.search(text)
        if m:
            year, month = now.year, now.month
            if m.group(1) and m.group(1).startswith("下"):
                month += 1
                if month > 12:
                    month, year = 1, year + 1
            day = min(int(m.group(2)), calendar.monthrange(year, month)[1])
            date_part = datetime(year, month, day)
            has_date = True

    if not has_date and not has_time:
        return None
    if fixed_dt is not None:  # 小时/分钟级偏移：时刻已含在结果里
        return ParseResult(dt=fixed_dt, has_date=has_date, has_time=has_time,
                           text=text.strip())
    if date_part is None:
        date_part = datetime(now.year, now.month, now.day)
    return ParseResult(
        dt=date_part.replace(hour=hour, minute=minute),
        has_date=has_date, has_time=has_time, text=text.strip(),
    )


def parse_dt(text: str, now: datetime | None = None) -> datetime | None:
    """便捷入口：只取 datetime 结果。"""
    r = parse(text, now)
    return r.dt if r else None
