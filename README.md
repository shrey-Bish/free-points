# Free Points

**Your syllabus owes you points.** A Cubbie Skill that reads every course on Canvas and finds the grade points
you're about to lose: unused late days, extra credit, dropped quizzes, attendance points and regrade windows. It
does the math, tells you which ones can lift your letter grade, and reminds you before each one expires.

Cubbie Hackathon, Track 1 (Cubbie Skills). Built by **Enrollment Goblins**.

▶ **[Watch the 1-minute video](https://www.tiktok.com/@user214186520884/video/7700649751108160799)** (TikTok)

## Install

Text this link to Cubbie and reply "yes":

```
https://github.com/shrey-Bish/free-points
```

Then ask: "am I leaving any points on the table?"

## What you get

```text
About 4.5 points still open across your 4 courses (1 point = 1% of your final grade).

1. MAT 265 Quiz 7 regrade: ask by Tue [Syllabus, Regrades]
2. PSY 101 Chapter 9 reflection: +0.5 by Thu [Announcement, Oct 20]
3. MAT 265 bonus homework set: +1 by Fri [Announcement, Oct 22]

Also: 2 late days left in CSE 340, and you can skip 1 more MAT 265 quiz.
PSY 101 research credit would take you from 89.2 to an A-.

Want a reminder Wednesday for the reflection?
```

Every line says where it came from, so you can check it. When the syllabus is unclear, Free Points doesn't guess:
it writes down the question to ask your professor and offers to draft the email.

## Why students need it

Everyone skims the syllabus in week one. By week twelve, nobody remembers that the lowest two quizzes drop, that
late days expire at the end of classes, or that regrade requests close a week after grades come out. Those rules
are worth real points, and they're written down, just never in front of you when they matter.

## How it works

1. Cubbie reads each course's syllabus, pages, recent announcements and gradebook on Canvas (already connected,
   no sign-in).
2. It writes every points policy it finds, each with its source and a short quote, following
   [`references/policy-types.md`](references/policy-types.md).
3. [`scripts/free_points.py`](scripts/free_points.py) does the exact math: converts raw points to a share of the
   final grade, counts late days and free skips left, works out regrade deadlines, ranks what's still open and checks
   which open points reach the next letter grade.
4. Cubbie texts the top three and offers a reminder or a weekly Sunday check-in that only speaks up when something
   expires that week.

It never does graded work, never submits anything, and never emails a professor without your yes.

## Try the math without Cubbie

```bash
python3 scripts/free_points.py --sample           # four sample courses
python3 scripts/free_points.py --sample --week    # only what expires in 7 days
python3 -m unittest discover -s tests             # 12 tests, standard library only
```

The sample courses in `assets/` are made up.

## Privacy

Your course data stays on your own Cubbie drive in `~/.config/free-points/`. The script makes no network calls.
Say "forget my Free Points data" to delete it.
