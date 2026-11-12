<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Templates Layer

Stores reusable templates, standard prompts, card formats, and data contracts that help this repository stay structurally aligned with the prototype in the technical report.

- [`basic/`](basic/README.md): start here. Short skeletons for every kind of card, in English and Chinese: research identity, direction summary, project, paper, decision, working style, heuristic, mental model, person, feedback, meeting, review, grant and message. [examples/starter-cards/](../examples/starter-cards/en/README.md) shows how they look filled in.
- `paper-template.md`, `person-template.md`, `project-template.md`, `talk-template.md`: the same cards as the matching skeletons in `basic/` (a talk card follows the same conventions), followed by optional later sections such as the public boundary, what the card does not prove and the next upgrade action. Add those sections once a card is used across projects; there is no second template family.
- `new-project-intake-card-template.md`, `research-expression-task-brief.md`, `safe-export-template.md`, `eval-case-template.md`, `self-evolution-report-template.md`, `memory-update-report-template.md`, `workflow-template.md`: project intake, expression task, safe export, eval, self-evolution, and writeback templates.
- `external-capability-source-candidate.md`: records external skill/repository links, versions, licenses, transformation or composition hypotheses, smallest tests, and destination owners before any plugin is created or installed.
- `derived-work-artifact-template.md` / `derived-work-artifact-template.zh.md`: working and archived forms for bounded presentation, meeting, application, analysis, or revision artifacts in a private/local vault.
- `standard-agent-prompts.en.md`: English standard agent prompts for onboarding, paper cards, collaborator extraction, talk cards, relation cards, plan cards, and inbox processing.
- `standard-agent-prompts.zh.md`: Chinese standard agent prompts.
- `data_contracts/`: data contracts for generated data and frontend/backend interaction.
  - `data_contracts/researchos-extension-contract-v1.md`: extension protocol for new categories, resource objects, workflow objects, and dashboard surfaces.
