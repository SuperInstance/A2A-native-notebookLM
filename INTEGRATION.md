# A2A-native-notebookLM — Integration Map

## Overview

A2A-native-notebookLM is the **workspace layer** for the SuperInstance ecosystem. It provides a collaborative notebook environment where agents automate workflows, co-author with humans, and organize knowledge.

## Wiring Diagram

```
openmind (cells → notebook sections)
  │
  ▼
A2A-native-notebookLM ◄── t-minus (scheduled automations)
  │                     ◄── fleet-warden (health monitoring)
  │
  ├──► agent_automation: extract, summarize, transform, alert
  ├──► self_service: agents create their own automations
  └──► collaborative_notebook: shared authoring space
```

## Integration Points

### openmind — Cells Become Notebook Sections

openmind decomposes codebases into cells. In A2A-native-notebookLM, each cell becomes a notebook section:

- **Cell → Section** — A cell's interface, provides, and budget are rendered as a structured notebook section.
- **Cross-references** — Dependencies between cells become notebook cross-links.
- **Live updates** — When a cell changes, its notebook section updates automatically.

Agents can navigate the notebook to understand the entire system's decomposition without leaving the workspace.

### t-minus — Scheduled Automations

t-minus provides the scheduling layer for notebook automations:

- **Scheduled extraction** — Periodically pull data from external sources into notebook sections.
- **Recurring summaries** — Generate summaries of cell activity on a schedule.
- **Alert rules** — Trigger notifications when cell metrics exceed thresholds.
- **Self-service** — Agents create their own t-minus automations without human approval for routine tasks.

### fleet-warden — Health Monitoring

fleet-warden monitors the health of all automations:

- **Automation health** — Is the scheduled extraction still running? Did the last summary succeed?
- **Alert fatigue detection** — Are automations generating too many notifications?
- **Resource usage** — Are automations staying within their conservation budgets?
- **Auto-remediation** — For known failure modes, fleet-warden can restart or adjust automations.

## Workspace Model

### Sections

A notebook is organized into sections. Each section corresponds to a cell, topic, or automation:

```
Section {
  title: string
  source: cell_name | "manual" | "automation"
  content: markdown | code | data
  automations: list[automation_id]
  health: fleet_warden_status
}
```

### Automations

Automations are first-class workspace objects:

```
Automation {
  type: "extraction" | "summary" | "transform" | "alert"
  schedule: t_minus_schedule
  source: section | external_url | cell
  target: section
  health: fleet_warden_status
}
```

### Collaboration

Humans and agents co-author in the same space:

- **Shared sections** — Both can edit, annotate, and comment.
- **Agent drafts** — Agents can create draft sections for human review.
- **Review workflow** — Changes to critical sections require human approval.
- **Attribution** — Every edit is attributed to human or agent.
