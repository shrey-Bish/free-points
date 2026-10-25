---
name: free-points
description: Finds grade points a student is about to lose, like unused late days, extra credit, dropped quizzes, attendance points and regrade windows, by reading their Canvas syllabi. Use it whenever the student asks about extra credit, bonus points, late days or tokens, whether they can skip a quiz or a class, how to raise or bump a grade, a regrade deadline, what the syllabus says about late work or dropped scores, "free points" or "am I leaving points on the table", even if they never say "syllabus". Also runs its own weekly check-in about points that expire soon. It finds and explains points the course already offers; it never does graded work.
---

# Free Points

Every syllabus hides points: late days that vanish after the last week, a 1% survey, the lowest quiz that drops,
one week to ask for a regrade. Students skim the syllabus once in week one and lose them. This Skill reads every
course for the student, does the math in a script, and reminds them before each one expires.

## When to use

- "Am I leaving any points on the table?"
- "Is there any extra credit in PSY 101?"
- "Do I have late days left in CSE 340?"
- "Can I skip Friday's quiz?"
- "I'm at an 89, how do I get an A-?"
- "Is it too late to ask for a regrade on Quiz 7?"

Do not use it to do assignments, write answers or ask for points the course doesn't offer. For a study plan, use
Cubbie's `study-plan-builder`. For an email to a professor, hand the draft to Cubbie's `email-to-professor`.

## What it uses

- **Canvas** (connected): courses, syllabus, course pages and files, announcements, the gradebook and submissions.
- **Reminders and scheduled check-ins**: an optional weekly check-in and one-off reminders before a deadline.
- **Memory**: the check-in time and any course the student asked to leave out.
- **Code sandbox**: `scripts/free_points.py`, plain Python 3 with no packages, so there is no setup.

If Canvas is not connected, say so in one line and offer two choices: connect Canvas, or send the syllabi (PDFs or
photos) plus the current grades if they know them. Then continue with what they send.

## Steps

1. **Pick the courses.** Use this term's courses from Canvas, or only the one the student named. Leave out any
   course the student asked to skip before.

2. **Read each course.** In this order, and stop looking for a policy once you have its source:
   - the syllabus page, then any course file with "syllabus" in its name (PDF or Word)
   - the course home page and pages about grading, exams or late work
   - announcements from the last 60 days that mention extra credit, bonus, late days, drops, regrades or surveys
   - the gradebook: assignment groups and weights, the current total, each item's score, points possible,
     submitted or late flags and when its grade came out

3. **Write what you found.** Read `references/policy-types.md` first, then write every course into
   `~/.config/free-points/courses.json` (create the folder if needed). Each policy needs a source and a short exact
   quote. When the syllabus is unclear, keep the policy, leave the numbers out and put the question for the
   professor in `unclear`. Never invent a number or a date.

4. **Do the math.** From this Skill's folder, with the student's local date (the sandbox clock may be in another
   time zone):

   ```bash
   python3 scripts/free_points.py --today <YYYY-MM-DD>
   ```

   Add `--course "<name>"` when the student asked about one course. Add `--json` if you need the numbers. The
   script ranks what is still open, soonest first, adds up the bonus points, and says when the open points are
   enough to reach the next letter grade.

5. **Reply** following the rules below.

6. **Offer one follow-up**, then stop:
   - If something is worth 1 point or more and due within 7 days, offer a reminder 2 days before it (or the
     morning of, if that's sooner). Create it only after the student says yes.
   - Otherwise, offer the weekly check-in once: "Want a heads-up every Sunday at 7 pm when points are about to
     expire?" Let the student pick the day and time, remember it, and create the check-in only after they agree.
     Word the check-in so it makes sense later on its own:
     "Free Points weekly check: re-read Canvas grades, submissions and new announcements for my courses, update
     ~/.config/free-points/courses.json as the free-points Skill describes, run
     `python3 scripts/free_points.py --today <today> --week` from the free-points Skill folder, and text me only
     what expires in the next 7 days. If the script says nothing expires, send nothing."

7. **Anything that needs the professor** (using a late day by request, a regrade request, asking whether a bonus
   is still open): offer to draft it with `email-to-professor`, show the draft, and send only after the student
   says yes. Never submit work, claim a late day or file a regrade on the student's behalf.

## Replies

Short, plain text, no Markdown symbols, one idea per message.

- Lead with the total and what a point means: "About 4.5 points still open across your 4 courses (1 point = 1% of
  your final grade)."
- Then the top three, soonest first, one line each: course, what it is, what it's worth, the deadline, and the
  source in brackets.
- Then one line for anything that isn't points but still helps: late days left, a quiz they can skip, a score the
  final can replace.
- Mention a grade bump when the script finds one: "That's enough to take PSY 101 from 89.2 to an A-."
- More than six items: make a one-page PDF called "Free Points" with the full list and text only the top three.
- If the script lists questions for the professor, mention the count and offer to draft them.
- End with one question (the reminder, the check-in or a draft), never more than one.

Example:

```text
About 4.5 points still open across your 4 courses (1 point = 1% of your final grade).

1. MAT 265 Quiz 7 regrade: ask by Tue [Syllabus, Regrades]
2. PSY 101 Chapter 9 reflection: +0.5 by Thu [Announcement, Oct 20]
3. MAT 265 bonus homework set: +1 by Fri [Announcement, Oct 22]

Also: 2 late days left in CSE 340, and you can skip 1 more MAT 265 quiz.
PSY 101 research credit would take you from 89.2 to an A-.

Want a reminder Wednesday for the reflection?
```

## When something fails

| Exit code | Meaning | What to text |
| --- | --- | --- |
| 2 | No course file yet | Nothing: go back to steps 2 and 3, then run again |
| 3 | The course file has a problem | Fix the fields the script names and run again; if it still fails, say the math didn't work and list what you found without numbers |
| 4 | Nothing open (or, with `--week`, nothing expiring) | "I read your syllabi and didn't find open extra credit, late days, drops or regrade windows." In a check-in, send nothing |
| 5 | No course matches `--course` | Ask which course they meant, listing the ones on file |

- If a syllabus can't be found for a course, say which one and ask the student to send it as a PDF or a photo.
- Never state a policy without its source. If the syllabus doesn't mention extra credit, say so plainly instead of
  guessing.

## Privacy

Everything stays on the student's own Cubbie drive in `~/.config/free-points/`. The script makes no network calls.
Saying "forget my Free Points data" means deleting that folder.
