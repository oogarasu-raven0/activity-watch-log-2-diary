from datetime import datetime, timedelta, time, timezone
from collections import defaultdict
import re
import argparse

SESSION_GAP = timedelta(seconds=60)
MAX_SESSION_DURATION = timedelta(hours=1)  # ← 1時間にしたければ hours=1
LOG_PATH = "aw-watcher.log"

MERGE_GAP = timedelta(seconds=30)
MIN_DURATION = timedelta(seconds=5)
JST = timezone(timedelta(hours=9))
DAY_CUTOFF = time(2, 0)
MAX_URL_LENGTH = 200

EXCLUDED_APPS = {
    ("Android", "Pixel Launcher"),
}

LOG_RE = re.compile(
    r"- (?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\((?P<duration>\d+:\d{2}:\d{2})\) "
    r"\{'app': '(?P<app>[^']+)', 'title': '(?P<title>[^']*)'\}"
)

AFK_RE = re.compile(
    r"- (?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\((?P<duration>\d+:\d{2}:\d{2})\) "
    r"\{'status': '(?P<status>afk|not-afk)'\}"
)

ANDROID_EVENT_RE = re.compile(
    r"- (?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\((?P<duration>\d+:\d{2}:\d{2})\) "
    r"\{'app': '(?P<app>[^']+)', "
    r"'classname': '(?P<classname>[^']+)', "
    r"'package': '(?P<package>[^']+)'\}"
)

ESCAPED_ZERO_WIDTH_RE = re.compile(
    r"\\u200[b-d]|\\u2060|\\ufeff",
    re.IGNORECASE
)

ZERO_WIDTH_RE = re.compile(
    r"[\u200B\u200C\u200D\u2060\uFEFF]"
)

ANDROID_WEB_EVENT_RE = re.compile(
    r"- (?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\((?P<duration>\d+:\d{2}:\d{2})\) "
    r"\{'audible': (?P<audible>True|False), "
    r"'incognito': (?P<incognito>True|False), "
    r"'title': '(?P<title>[^']*)', "
    r"'url': '(?P<url>[^']+)'\}"
)

def clean_text(s: str) -> str:
    if not s:
        return s
    # エスケープ表現を先に消す
    s = ESCAPED_ZERO_WIDTH_RE.sub("", s)
    # 実体のゼロ幅文字を消す
    s = ZERO_WIDTH_RE.sub("", s)
    # 空白整理
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def parse_duration(s: str) -> timedelta:
    h, m, sec = map(int, s.split(":"))
    return timedelta(hours=h, minutes=m, seconds=sec)

def living_date(dt: datetime):
    if dt.time() < DAY_CUTOFF:
        return (dt - timedelta(days=1)).date()
    return dt.date()

def common_suffix(strings):
    if not strings:
        return ""

    split = [s.split(" - ") for s in strings]
    min_len = min(len(s) for s in split)

    suffix = []
    for i in range(1, min_len + 1):
        parts = {s[-i] for s in split}
        if len(parts) == 1:
            suffix.insert(0, parts.pop())
        else:
            break

    return " - ".join(suffix)

from urllib.parse import urlsplit, urlunsplit

def strip_query(url: str) -> str:
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return url

def normalize_url_for_title(url: str) -> str:
    try:
        parts = urlsplit(url)
        base = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        if len(base) > MAX_URL_LENGTH:
            return parts.netloc
        return base
    except Exception:
        return url
parser = argparse.ArgumentParser()
parser.add_argument("--today", action="store_true")
args = parser.parse_args()

events = []

is_android = False

platform = "Desktop"

with open(LOG_PATH, encoding="utf-16le", errors="ignore") as f:
    for line in f:
        line = clean_text(line.rstrip())

        if line == "Android":
            is_android = True
            continue

        if is_android and line == "events:":
            continue

        # --- Desktop / AFK ---
        if not is_android:
            m = LOG_RE.search(line)
            m_afk = AFK_RE.search(line)

            if not m and not m_afk:
                continue

            if m:
                start_utc = datetime.strptime(
                    m.group("time"), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)

                start = start_utc.astimezone(JST)
                dur = parse_duration(m.group("duration"))

                if dur < MIN_DURATION:
                    continue

                app = m.group("app")
                title = m.group("title")
                if (platform, app) in EXCLUDED_APPS:
                    continue
                if not title:
                    continue

                platform = "Desktop"

            else:
                start_utc = datetime.strptime(
                    m_afk.group("time"), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)

                start = start_utc.astimezone(JST)
                dur = parse_duration(m_afk.group("duration"))

                if dur < MIN_DURATION:
                    continue

                status = m_afk.group("status")
                app = "AFK" if status == "afk" else "Active"
                title = "離席" if status == "afk" else "操作中"
                platform = "Desktop"

        # --- Android ---
        else:
            m_android = ANDROID_EVENT_RE.search(line)
            m_android_web = ANDROID_WEB_EVENT_RE.search(line)

            if not m_android and not m_android_web:
                continue

            # --- Android App Event ---
            if m_android:
                start_utc = datetime.strptime(
                    m_android.group("time"), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)

                start = start_utc.astimezone(JST)
                dur = parse_duration(m_android.group("duration"))

                if dur < MIN_DURATION:
                    continue

                app = m_android.group("app")
                classname = m_android.group("classname")

                if (platform, app) in EXCLUDED_APPS:
                    continue

                title = classname
                platform = "Android"

            # --- Android Web Event ---
            # --- Android Web Event ---
            else:
                start_utc = datetime.strptime(
                    m_android_web.group("time"), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)

                start = start_utc.astimezone(JST)
                dur = parse_duration(m_android_web.group("duration"))

                if dur < MIN_DURATION:
                    continue

                app = "Browser"
                raw_title = m_android_web.group("title")
                url = m_android_web.group("url")

                if raw_title:
                    title = raw_title
                else:
                    title = normalize_url_for_title(url)

                platform = "Android"

            events.append((start, start + dur, platform, app, title))

        events.append((start, start + dur, platform, app, title))

events.sort(key=lambda x: x[0])

blocks = []
for ev in events:
    if not blocks:
        blocks.append(list(ev))
        continue

    last = blocks[-1]

    same_app = ev[2] == last[2]
    same_title = ev[3] == last[3]
    gap_ok = ev[0] - last[1] <= MERGE_GAP

    if same_app and same_title and gap_ok:
        last[1] = max(last[1], ev[1])
    else:
        blocks.append(list(ev))

by_date = defaultdict(list)
for b in blocks:
    by_date[living_date(b[0])].append(b)

def blocks_to_sessions(blocks):
    sessions = []

    for b in blocks:
        if not sessions:
            sessions.append([b])
            continue

        last_session = sessions[-1]
        last_block = last_session[-1]

        session_start = last_session[0][0]
        session_end_if_added = max(last_block[1], b[1])

        gap_ok = b[0] - last_block[1] <= SESSION_GAP
        duration_ok = session_end_if_added - session_start <= MAX_SESSION_DURATION

        if gap_ok and duration_ok:
            last_session.append(b)
        else:
            sessions.append([b])

    return sessions

from collections import defaultdict

def summarize_session(session):
    start = session[0][0]
    end = session[-1][1]
    duration = int((end - start).total_seconds())

    app_time = defaultdict(int)
    app_titles = defaultdict(set)

    for b in session:
        b_dur = int((b[1] - b[0]).total_seconds())
        platform = b[2]
        app = f"{platform}:{b[3]}"
        title = b[4]

        app_time[app] += b_dur
        app_titles[app].add(title)

    return {
        "start": start,
        "end": end,
        "duration": duration,
        "app_time": app_time,
        "app_titles": app_titles,
    }

by_date_sessions = defaultdict(list)

for d, blocks_in_day in by_date.items():
    sessions = blocks_to_sessions(blocks_in_day)
    by_date_sessions[d] = sessions

# --- today フィルタ（安全版） ---
output_dates = by_date

if args.today:
    now_jst = datetime.now(JST)
    today_key = living_date(now_jst)
    output_dates = {}
    if today_key in by_date:
        output_dates[today_key] = by_date[today_key]

# --- 出力 ---
for d in sorted(output_dates.keys()):
    print(d.isoformat())

    for session in by_date_sessions.get(d, []):
        s = summarize_session(session)

        print(
            f"{s['start'].strftime('%H:%M:%S')}"
            f"-{s['end'].strftime('%H:%M:%S')} "
            f"({s['duration']}s)"
        )

        for app, sec in sorted(
            s["app_time"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            titles = list(s["app_titles"][app])
            suffix = common_suffix(titles)

            # content が複数あるときだけスリム化
            if suffix and len(titles) > 1:
                slimmed = []
                mark = " - " + suffix
                for t in titles:
                    if t.endswith(mark):
                        slimmed.append(t[: -len(mark)])
                    else:
                        slimmed.append(t)
            else:
                slimmed = titles
                suffix = None  # ← 1件のときは suffix を無効化

            print(f"  {app}: {sec}s")

            is_android = app.startswith("Android:")
            is_android_browser = app == "Android:Browser"

            if not is_android or is_android_browser:
                print(f"    content: {' / '.join(slimmed)}")

                if suffix:
                    print(f"      (in {suffix})")

    print()

