# Basic card templates

Blank skeletons for the cards a vault needs. Each one has a short "How to fill in" note under its frontmatter that says where the file goes and what each value means; delete the note when the card is done. For filled-in versions, see the [example cards](../../examples/starter-cards/en/README.md), which also explain the three layers in a card, maturity and sensitivity.

| Template | Card | Goes in |
| --- | --- | --- |
| [research-identity.md](research-identity.md) | Research identity, the entry to the whole vault | `personal_vault/00_identity/` |
| [boundaries.md](boundaries.md) | What never goes to an assistant, what is not said outside, rules on AI tools, who approves; read before anything goes out | `personal_vault/00_identity/boundaries.md` |
| [capsule.md](capsule.md) | Direction summary, the entry to one direction | `personal_vault/01_knowledge/capsules/` |
| [project.md](project.md) | Project | `personal_vault/01_knowledge/projects/` |
| [paper.md](paper.md) | Paper or other source | `personal_vault/01_knowledge/papers/` |
| [outputs-index.md](outputs-index.md) | All your outputs, their status and what may be said about each; read at the evidence level | `personal_vault/01_knowledge/papers/outputs-index.md` |
| [decision.md](decision.md) | Decision | `personal_vault/02_decisions/` |
| [style.md](style.md) | Working style for one kind of task (writing, review, proposal, figures and talks, mentoring) | `personal_vault/03_cognition/style/<task>.md` |
| [heuristic.md](heuristic.md) | A working habit | `personal_vault/03_cognition/heuristics/` |
| [mental-model.md](mental-model.md) | A model of how something in your field works | `personal_vault/03_cognition/mental_models/` |
| [person.md](person.md) | Person; your own profile uses it too | `personal_vault/04_people/collaborators/`, or `00_identity/profile.md` |
| [author-roles.md](author-roles.md) | Who did what on each output, only from a contribution statement or your own words; read at the evidence level | `personal_vault/01_knowledge/papers/author-roles.md` |
| [feedback.md](feedback.md) | Feedback on a student's or mentee's progress | `personal_vault/04_people/feedback/` |
| [meeting.md](meeting.md) | Meeting or other event | `personal_vault/06_active_context/meetings/` |
| [review.md](review.md) | Your comments on a manuscript you review | `personal_vault/06_active_context/reviews/` |
| [grant.md](grant.md) | One grant application | `personal_vault/06_active_context/grants/` |
| [message.md](message.md) | A draft academic email or message | `personal_vault/06_active_context/messages/` |

Keep the frontmatter values on one line each, without trailing `#` comments: a comment after a value is read as part of it. The full templates one level up (`../paper-template.md`, `../person-template.md`, `../project-template.md`, `../talk-template.md`) are the same cards with optional later sections for when a card is used across projects; start from these.
