# Example cards (English)

These twelve fictional cards tell one story: a researcher in visual tracking learns at a meeting that a benchmark is about to change and decides to postpone a set of experiments; a working-style card records how they write the paper, a boundary card what must not go out, and two indexes what may be said about each output and who did what. Each card can be copied and rewritten as your own; the matching blank skeletons are in [`09_templates/basic/`](../../../09_templates/basic/README.md). The cards are for reference only and are never copied into your `personal_vault/`.

**Not in visual tracking? The cards still fit.** The example field is visual tracking, but the same cards map onto other research. In a survey study, a "paper card" can record one version of a questionnaire, and the example's "benchmark version" is like a new questionnaire wave or a revised set of items. In an archive project, a paper card can record an archive catalogue or a critical edition, and a new benchmark version is like the archive publishing a corrected catalogue. In a lab study, a paper card can record a protocol, and a new benchmark version is like an amended protocol. Project, decision, person and meeting cards keep their names and record your projects, decisions, collaborators and meetings as they are.

| Card | Where it goes | What it records |
| --- | --- | --- |
| [Research identity](00_identity/research-identity.md) | `00_identity/` | Who you are, your current mainline, how you work; an assistant reads this page first |
| [Boundary card](00_identity/boundaries.md) | `00_identity/` | What never goes to an assistant, what is not said outside, rules on AI tools, who approves |
| [Direction summary](01_knowledge/capsules/occlusion-tracking-capsule.md) | `01_knowledge/capsules/` | The entry to one direction: current points and which card to read for which task |
| [Outputs index](01_knowledge/papers/outputs-index.md) | `01_knowledge/papers/` | Each output, its status, what may be said outside and what not yet |
| [Project card](01_knowledge/projects/occlusion-tracking.md) | `01_knowledge/projects/` | Research question, current progress, results so far |
| [Paper card](01_knowledge/papers/example-benchmark.md) | `01_knowledge/papers/` | Which version you read, what the paper says, your view |
| [Decision card](02_decisions/2026-09-22-wait-for-benchmark-v2.md) | `02_decisions/` | Options, why this one, the risks accepted |
| [Heuristic card](03_cognition/heuristics/check-benchmark-version-first.md) | `03_cognition/heuristics/` | One of your working habits: the rule, when to use it, when not to |
| [Working-style card](03_cognition/style/writing.md) | `03_cognition/style/` | How you do one kind of task, here writing: each point with why, how to apply and its source, apart from the assistant's guesses |
| [Person card](04_people/collaborators/lin-ke.md) | `04_people/collaborators/` | Sourced background, evidenced relationship, interactions |
| [Author roles](01_knowledge/papers/author-roles.md) | `01_knowledge/papers/` | Who did what on each output, each with its source |
| [Meeting card](06_active_context/meetings/2026-09-22-benchmark-sync.md) | `06_active_context/meetings/` | A meeting: who said what, your view, what was decided, action items |

The boundary card is read before anything goes out: a talk, a proposal, an email to someone outside, an export, a review. The outputs index and the author-roles card are read at the evidence level, to check a claim or a contribution before formal writing, a proposal or a CV.

## Three layers in a card

An assistant reads your vault from the surface down and stops as soon as a layer is enough. Cards are written to support that.

- **Layer 1: summaries.** The frontmatter and the `Agent Summary`. This paragraph has to stand on its own: what this is, where it stands, when to read the card and what not to use it for. The research identity page is the entry to the whole vault and a direction summary is the entry to one direction; both point a task to the cards it needs. A summary's table names the cards, but packing a direction summary hands over only that page; the assistant fetches each card it needs with `python3 scripts/ros.py --root personal_vault context <card path>`, so that the context receipt covers it.
- **Layer 2: card bodies.** Read only when the task needs the detail.
- **Layer 3: evidence.** Originals, notes and experiment logs stay where they are; the card's "Evidence boundary" says where, and they are not read by default. They are read only to verify something before formal writing or external use.

These three layers are about how deep the assistant goes inside one card. They are not the same as the three reading levels quick, standard and evidence of `python3 scripts/plan_context.py <task> --vault personal_vault --mode quick|standard|evidence`: those decide which cards are read, and the command lists, for each level, which of your cards the assistant reads and which ones you have not written yet.

## Maturity

Each card type carries one field for how far it has grown: `analysis_state` M1 to M3 for papers and talks, `project_maturity` I0 to I3 for projects, `relationship_maturity` R0 to R3 for people, `group_level` G0 to G2 for direction summaries; heuristics use `confidence` and `status` (provisional, stable), and working-style cards only `status` (provisional, confirmed). A card moves up only when its sources, links and confirmations grow, not when it gets longer. These codes (such as `M1_registered`, `I1_sandbox` or `G2_direction_abstraction`) are optional labels; if you would rather not think about them, leave the skeleton's default: `ros` does not read them, and only the optional Dashboard uses them to show how far a card has grown. The levels are explained once, in the [card maturity rubric](../../../08_exports/public_starter/onboarding-card-maturity-rubric.md).

## Sensitivity

`sensitivity` decides whether `ros context` includes the card in what it packs for an assistant:

- `public`, `internal`: included. Use `internal` for papers, projects, decisions, summaries, heuristics, working-style cards, the boundary card and the outputs index.
- `sensitive`: left out when the assistant runs `ros context`. Use it for cards about real people (including the author-roles card) and records of what others said. When the assistant reports such a card excluded, it should tell you so and not open the file directly instead; if a task really needs it, run `python3 scripts/ros.py --root personal_vault context <card>` in your own terminal, answer `y`, and copy to the assistant only the part the task needs.
- `private`: never packed. Use it only for a card you never want `ros context` to hand to an assistant.

The label does not stop an assistant from opening the file itself; see "Where your material goes" in the README.

## Markers in the text

- **(fact)**: content with a source you can check.
- **My view**: your own reading, written apart from what others said.
- **Assistant's additions (not confirmed by me)**: an assistant's guesses, not to be relied on until confirmed.
- **To verify**: things not yet confirmed.

To keep "My view" as a durable judgment, the assistant proposes it with `ros propose judgment`. Once you agree, it pastes the change that `ros admit` prints into the card, and you then confirm it in your own terminal with `ros admit --confirm`. The examples deliberately contain no judgment block; how a judgment comes back for review after a source changes is shown by the walk-through in Section 3 of the user manual. Cards in the cognition layer (working style, heuristics), the research identity page and the boundary card describe how you work, so an assistant shows you its draft and writes it only after you agree.
