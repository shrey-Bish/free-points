#!/usr/bin/env python3
"""Free Points: rank the grade points a student can still collect.

Cubbie reads each course's syllabus and grades, writes them as JSON in the shape described in
references/policy-types.md, and runs this script to do the math: what each item is worth to the
final grade, when it expires, and whether it is enough to reach the next letter grade.

Standard library only. Nothing is sent anywhere.

    python3 scripts/free_points.py --today 2026-10-25
    python3 scripts/free_points.py --today 2026-10-25 --week
    python3 scripts/free_points.py --today 2026-10-25 --course "MAT 265"
    python3 scripts/free_points.py --sample

Exit codes: 0 ok, 2 no course file yet, 3 the course file is not valid,
4 nothing to report, 5 no course matches --course.
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.normpath(os.path.join(HERE, "..", "assets", "sample_courses.json"))
STATE = os.path.join(os.path.expanduser("~"), ".config", "free-points", "courses.json")
SOON_DAYS = 7

TYPES = {
    "extra_credit", "late_days", "drop_lowest", "attendance",
    "regrade_window", "replace_score", "resubmission", "other",
}
BONUS_TYPES = {"extra_credit", "resubmission", "other"}  # count toward the "still open" total


class Invalid(Exception):
    pass


# ---------- small helpers ----------

def num(value, field, where):
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Invalid(f"{where}: {field} should be a number, got {value!r}")
    return float(value)


def day(value, field, where):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise Invalid(f"{where}: {field} should be a date like 2026-12-04, got {value!r}")


def show_day(d):
    return f"{d:%a} {d:%b} {d.day}"


def pts(v):
    v = round(v + 1e-9, 1)
    return str(int(v)) if v == int(v) else f"{v:.1f}"


def status_for(deadline, today):
    if deadline is None:
        return "open"
    if deadline < today:
        return "expired"
    if (deadline - today).days <= SOON_DAYS:
        return "soon"
    return "open"


# ---------- one policy -> one or more items ----------

def evaluate(policy, course, today):
    where = f"{course['course']} / {policy.get('title') or policy.get('type')}"
    kind = policy.get("type")
    if kind not in TYPES:
        raise Invalid(f"{where}: type should be one of {', '.join(sorted(TYPES))}, got {kind!r}")
    base = {
        "course": course["course"],
        "type": kind,
        "title": policy.get("title") or kind.replace("_", " "),
        "source": policy.get("source") or "",
        "quote": policy.get("quote") or "",
        "claim": policy.get("claim") or "",
        "unclear": policy.get("unclear") or "",
        "value": None,       # points = percentage points of the final grade
        "upside": None,      # "up to" points that depend on a future score
        "note": "",
        "deadline": day(policy.get("deadline"), "deadline", where),
    }
    items = []

    if kind == "extra_credit":
        worth = num(policy.get("worth_percent"), "worth_percent", where)
        if worth is None:
            p = num(policy.get("worth_points"), "worth_points", where)
            total = num(course.get("course_total_points"), "course_total_points", where)
            if p is not None and total:
                worth = p / total * 100
        earned = num(policy.get("earned_percent"), "earned_percent", where) or 0.0
        if worth is not None:
            base["value"] = max(0.0, worth - earned)
            if earned:
                base["note"] = f"{pts(earned)} of {pts(worth)} done"
        if policy.get("condition"):
            base["note"] = (base["note"] + "; " if base["note"] else "") + f"only {policy['condition']}"
        st = policy.get("status", "open")
        if st == "done" or (base["value"] == 0 and worth is not None):
            base["status"] = "done"
        elif st == "missed":
            base["status"] = "expired"
        else:
            base["status"] = status_for(base["deadline"], today)
        items.append(base)

    elif kind == "late_days":
        total = num(policy.get("total"), "total", where)
        used = num(policy.get("used"), "used", where) or 0.0
        if total is None:
            raise Invalid(f"{where}: late_days needs total")
        left = int(total - used)
        penalty = num(policy.get("penalty_percent"), "penalty_percent", where)
        weight = num(policy.get("typical_assignment_percent"), "typical_assignment_percent", where)
        noun = policy.get("unit") or "late day"
        base["note"] = f"{left} {noun}{'' if left == 1 else 's'} left"
        if left > 0 and penalty and weight:
            base["note"] += f", each saves about {pts(penalty / 100 * weight)} on a late {policy.get('applies_to') or 'assignment'}"
        base["status"] = "used" if left <= 0 else status_for(base["deadline"], today)
        items.append(base)

    elif kind == "drop_lowest":
        cat = policy.get("category") or "items"
        weight = num(policy.get("category_weight_percent"), "category_weight_percent", where)
        count_total = num(policy.get("count_total"), "count_total", where)
        dropped = num(policy.get("count_dropped"), "count_dropped", where)
        zeros = num(policy.get("missed_or_zero"), "missed_or_zero", where) or 0.0
        remaining = num(policy.get("remaining"), "remaining", where)
        if dropped is None:
            raise Invalid(f"{where}: drop_lowest needs count_dropped")
        skips = int(dropped - zeros)
        if remaining is not None:
            skips = min(skips, int(remaining))
        each = ""
        if weight and count_total and count_total > dropped:
            each = f", each counted one is worth {pts(weight / (count_total - dropped))}"
        one = policy.get("item_name") or f"of the {cat}"
        if skips > 0:
            base["note"] = f"you can skip {skips} more {cat if skips > 1 else one} at no cost; lowest {int(dropped)} drop{each}"
            base["status"] = status_for(base["deadline"], today)
        else:
            base["note"] = f"no free skips left in {cat} (lowest {int(dropped)} drop, already used)"
            base["status"] = "used"
        items.append(base)

    elif kind == "attendance":
        worth = num(policy.get("worth_percent"), "worth_percent", where)
        total = num(policy.get("sessions_total"), "sessions_total", where)
        left = num(policy.get("sessions_remaining"), "sessions_remaining", where)
        if worth is not None and total and left is not None:
            base["value"] = worth * left / total
            base["note"] = f"{int(left)} sessions left, about {pts(worth / total)} each, kept by showing up"
        base["status"] = "open" if left is None or left > 0 else "used"
        items.append(base)

    elif kind == "regrade_window":
        window = num(policy.get("window_days"), "window_days", where)
        graded = policy.get("items") or []
        if window is None:
            raise Invalid(f"{where}: regrade_window needs window_days")
        for g in graded:
            released = day(g.get("released"), "released", where)
            if released is None:
                continue
            it = dict(base)
            it["title"] = f"{g.get('name', 'graded work')} regrade request"
            it["deadline"] = released + timedelta(days=int(window))
            it["note"] = f"window closes {int(window)} days after grades came out"
            lost = num(g.get("points_lost_percent"), "points_lost_percent", where)
            if lost:
                it["upside"] = lost
            it["status"] = status_for(it["deadline"], today)
            items.append(it)
        if not graded:
            base["note"] = f"{int(window)} days after grades come out to ask for a regrade"
            base["status"] = "rule"
            items.append(base)

    elif kind == "replace_score":
        weight = num(policy.get("replaced_percent"), "replaced_percent", where)
        score = num(policy.get("replaced_score"), "replaced_score", where)
        what = policy.get("replaced_item") or "your lowest score"
        by = policy.get("by_item") or "the final"
        if weight is not None and score is not None:
            base["upside"] = weight * (100 - score) / 100
            base["note"] = f"if {by} beats your {what} score of {pts(score)}%"
        else:
            base["note"] = f"{by} can replace {what}"
        base["status"] = status_for(base["deadline"], today)
        items.append(base)

    else:  # resubmission, other
        worth = num(policy.get("worth_percent"), "worth_percent", where)
        base["value"] = worth
        st = policy.get("status", "open")
        base["status"] = "done" if st == "done" else "expired" if st == "missed" else status_for(base["deadline"], today)
        items.append(base)

    return items


# ---------- whole file ----------

def load(path):
    if not os.path.exists(path):
        print(f"No course file yet at {path}. Read the syllabi and grades first (see SKILL.md, step 3).")
        sys.exit(2)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"The course file at {path} is not valid JSON: {e}")
        sys.exit(3)
    if not isinstance(data, dict) or not isinstance(data.get("courses"), list):
        print('The course file needs a "courses" list (see references/policy-types.md).')
        sys.exit(3)
    return data


def next_cutoff(current, cutoffs):
    above = sorted((v, k) for k, v in cutoffs.items() if isinstance(v, (int, float)) and v > current)
    return above[0] if above else None


def analyse(data, today, course_filter=None):
    items, bumps, courses_seen = [], [], []
    problems = []
    for course in data["courses"]:
        if not isinstance(course, dict) or not course.get("course"):
            problems.append('every course needs a "course" name')
            continue
        if course_filter and course_filter.lower() not in course["course"].lower():
            continue
        courses_seen.append(course["course"])
        course_items = []
        for policy in course.get("policies") or []:
            try:
                course_items.extend(evaluate(policy, course, today))
            except Invalid as e:
                problems.append(str(e))
        items.extend(course_items)

        current = course.get("current_percent")
        cutoffs = course.get("letter_cutoffs") or {}
        if isinstance(current, (int, float)) and cutoffs:
            nxt = next_cutoff(float(current), cutoffs)
            open_bonus = sum(i["value"] for i in course_items
                             if i["type"] in BONUS_TYPES and i["status"] in ("open", "soon") and i["value"])
            if nxt:
                need = nxt[0] - float(current)
                bumps.append({
                    "course": course["course"], "current": float(current),
                    "next_letter": nxt[1], "next_cutoff": nxt[0],
                    "open_bonus": open_bonus, "short_by": max(0.0, need - open_bonus),
                })
    if problems:
        print("The course file has problems:")
        for p in problems[:5]:
            print(f"- {p}")
        sys.exit(3)
    return items, bumps, courses_seen


def order_key(i):
    return (0 if i["status"] == "soon" else 1,
            i["deadline"] or date.max,
            -(i["value"] or i["upside"] or 0))


def line(n, i):
    bits = [f"{i['course']}", i["title"]]
    if i["value"] and i["type"] == "attendance":
        bits.append(f"{pts(i['value'])} at stake")
    elif i["value"]:
        bits.append(f"+{pts(i['value'])}")
    elif i["upside"]:
        bits.append(f"up to +{pts(i['upside'])}")
    text = " · ".join(bits)
    if i["note"]:
        text += f" ({i['note']})"
    if i["deadline"]:
        text += f", by {show_day(i['deadline'])}"
    if i["source"]:
        text += f" [{i['source']}]"
    return f"{n}. {text}" if n else f"- {text}"


def report(items, bumps, courses, today, week):
    live = [i for i in items if i["status"] in ("open", "soon")
            and not (i["unclear"] and not i["value"] and not i["upside"] and not i["note"])]
    if week:
        live = [i for i in live if i["status"] == "soon"]
    live.sort(key=order_key)
    unclear = [i for i in items if i["unclear"]]

    if not live and not unclear:
        if week:
            print(f"Nothing expires in the next {SOON_DAYS} days.")
        else:
            print("No open extra credit, late days, drops or regrade windows found in these courses.")
        return 4

    bonus = sum(i["value"] for i in live if i["type"] in BONUS_TYPES and i["value"])
    upside = sum(i["upside"] for i in live if i["type"] == "replace_score" and i["upside"])
    out = [f"Free Points, {show_day(today)}"]
    if week:
        out.append(f"Expiring in the next {SOON_DAYS} days ({len(live)}):")
    else:
        head = f"About {pts(bonus)} point{'' if pts(bonus) == '1' else 's'} still open across {len(courses)} course{'s' if len(courses) != 1 else ''}"
        if upside:
            head += f", plus up to {pts(upside)} more from score replacement"
        out.append(head + " (1 point = 1% of a final grade).")
        out.append("")
        out.append("Soonest first:")

    for n, i in enumerate(live, 1):
        out.append(line(n, i))
        if i["claim"]:
            out.append(f"   how: {i['claim']}")

    if not week:
        reach = [b for b in bumps if b["open_bonus"] > 0]
        if reach:
            out.append("")
            out.append("Grade bumps:")
            for b in reach:
                if b["short_by"] == 0:
                    out.append(f"- {b['course']}: {pts(b['current'])}% now; the {pts(b['open_bonus'])} open would reach {b['next_letter']} ({pts(b['next_cutoff'])}%)")
                else:
                    out.append(f"- {b['course']}: {pts(b['current'])}% now; {pts(b['open_bonus'])} open, {pts(b['short_by'])} short of {b['next_letter']} ({pts(b['next_cutoff'])}%)")
        if unclear:
            out.append("")
            out.append("Ask the professor (the syllabus isn't clear):")
            for i in unclear:
                out.append(f"- {i['course']}: {i['unclear']}")
    print("\n".join(out))
    return 0


def to_json(items, bumps, today):
    def enc(i):
        j = dict(i)
        j["deadline"] = i["deadline"].isoformat() if i["deadline"] else None
        return j
    print(json.dumps({"today": today.isoformat(), "items": [enc(i) for i in items], "grade_bumps": bumps}, indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rank the grade points a student can still collect.")
    ap.add_argument("--today", help="the student's local date, YYYY-MM-DD")
    ap.add_argument("--input", help=f"course file (default {STATE})")
    ap.add_argument("--course", help="only this course (part of its name is enough)")
    ap.add_argument("--week", action="store_true", help=f"only items expiring in the next {SOON_DAYS} days")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--sample", action="store_true", help="use the bundled sample; never touches saved data")
    a = ap.parse_args(argv)

    path = SAMPLE if a.sample else (a.input or STATE)
    data = load(path)
    if a.today:
        try:
            today = date.fromisoformat(a.today)
        except ValueError:
            print(f"--today should look like 2026-10-25, got {a.today!r}")
            return 3
    elif a.sample and data.get("today"):
        today = date.fromisoformat(data["today"])
    else:
        today = date.today()

    items, bumps, courses = analyse(data, today, a.course)
    if a.course and not courses:
        print(f"No course matches {a.course!r}. Courses on file: {', '.join(c.get('course', '?') for c in data['courses'])}")
        return 5
    if a.json:
        return to_json(items, bumps, today)
    return report(items, bumps, courses, today, a.week)


if __name__ == "__main__":
    sys.exit(main())
