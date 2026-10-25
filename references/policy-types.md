# Reading a syllabus for free points

Read this before step 3 of `SKILL.md`. It says what to look for in each course and how to write it into
`~/.config/free-points/courses.json`, the file `scripts/free_points.py` reads.

## Ground rules

- **Only what the course says.** Use the syllabus, the course pages, announcements and the Canvas gradebook. Never
  use general knowledge about how courses "usually" work, and never invent a number.
- **Every policy has a source and a quote.** `source` says where it is ("Syllabus, Late work", "Announcement, Oct 22",
  "Course page: Exams"). `quote` is the shortest exact phrase that proves it, at most 25 words.
- **Unsure? Ask, don't guess.** When the wording is ambiguous ("bonus opportunities may be offered"), still add the
  policy, leave the numbers out, and put the question the student should ask in `unclear`.
- **Points mean percent of the final grade.** Convert when the course uses raw points: give `worth_points` and the
  course's `course_total_points`, and the script converts. If the course weights categories, a 10-point bonus inside a
  category worth 20% is not 10% of the grade; work out the share of the final grade, or leave `worth_percent` out and
  explain in `unclear`.
- **Counts come from Canvas.** Late days used, quizzes missed, sessions left and when grades came out come from the
  gradebook and submissions, not from the student's memory. If Canvas doesn't show it, leave the field out.
- **Dates are the student's dates**, `YYYY-MM-DD`. "One week after grades are released" for a quiz released Oct 20
  is written as the rule plus the release date; the script does the date math.

## What to look for

| Type | Words that signal it | Example |
| --- | --- | --- |
| `extra_credit` | extra credit, bonus, optional, research participation, SONA, survey, course evaluation, "up to x% added" | "Earn up to 3% by taking part in studies" |
| `late_days` | late days, grace days, slip days, tokens, late passes, "no questions asked" extensions | "3 late days for the semester" |
| `drop_lowest` | lowest dropped, best x of y, drop, replace a zero | "Your two lowest quiz scores are dropped" |
| `attendance` | attendance, participation, clicker, iClicker, Top Hat, in-class activities with a grade weight | "Attendance is 5% of the grade" |
| `regrade_window` | regrade, re-grade, grade dispute, "within x days of grades being posted", Gradescope requests | "Requests accepted for one week" |
| `replace_score` | final replaces, higher of, replaces your lowest exam, redemption | "The final replaces your lowest midterm if higher" |
| `resubmission` | resubmit, revise and resubmit, corrections for half credit back, test corrections | "Correct your exam for half the lost points" |
| `other` | anything else that adds points or saves them, such as a curve the student can affect | |

Skip curves the student can't influence, and policies that only take points away.

## The file

```json
{
  "term": "Fall 2026",
  "courses": [
    {
      "course": "MAT 265",
      "current_percent": 78.9,
      "letter_cutoffs": {"A": 90, "B+": 87, "B": 83, "B-": 80},
      "course_total_points": 1000,
      "policies": [ ...one object per policy... ]
    }
  ]
}
```

- `current_percent`: the course's current total in the Canvas gradebook, if Canvas shows one.
- `letter_cutoffs`: only from the syllabus. Leave it out if the syllabus doesn't list them.
- `course_total_points`: only for courses graded on raw points.

Every policy has `type`, `title` (a few words), `source`, `quote`, and optionally `deadline`, `claim` (how the student
gets it, in a few words) and `unclear` (a question for the professor). Then by type:

| Type | Fields |
| --- | --- |
| `extra_credit` | `worth_percent`, or `worth_points` with the course's `course_total_points`; `earned_percent` (already earned); `condition` ("if 80% of the class completes the evaluation"); `status`: `open`, `done` or `missed` |
| `late_days` | `total`, `used`, `unit` ("late day", "token"), `penalty_percent` (the penalty one late day avoids), `typical_assignment_percent` (what one assignment is worth in the final grade), `applies_to` ("project"); `deadline` = the last day they can be used |
| `drop_lowest` | `category` ("quizzes"), `item_name` ("quiz"), `category_weight_percent`, `count_total`, `count_dropped`, `missed_or_zero` (zeros or missed so far), `remaining` (still to come) |
| `attendance` | `worth_percent`, `sessions_total`, `sessions_remaining` |
| `regrade_window` | `window_days`; `items`: graded work still inside the window, each `{"name", "released", "points_lost_percent"}` (the last one optional) |
| `replace_score` | `replaced_item` ("Midterm 1"), `replaced_percent` (its weight), `replaced_score` (the student's percent on it), `by_item` ("the final exam"); `deadline` = the date of the replacing exam |
| `resubmission` | `worth_percent` (points recoverable), `status` |
| `other` | `worth_percent` if known |

For `regrade_window`, list only graded work released within the last `window_days` days, using the date the grade
appeared in Canvas. Leave `points_lost_percent` out unless the student says the grading was wrong; the Skill finds
the window, it doesn't judge the grading.

## Example

```json
{
  "type": "drop_lowest",
  "title": "quiz drops",
  "category": "quizzes",
  "item_name": "quiz",
  "category_weight_percent": 20,
  "count_total": 10,
  "count_dropped": 2,
  "missed_or_zero": 1,
  "remaining": 4,
  "source": "Syllabus, Quizzes",
  "quote": "Your two lowest quiz scores are dropped."
}
```

A full sample with four courses is in `assets/sample_courses.json`.
