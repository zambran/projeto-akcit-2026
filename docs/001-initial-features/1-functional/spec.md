# initial-features - Functional Spec

**Status**: approved
**Owner**: Lucas Zambrano Barboza
**Created**: 2026-05-01
**Last Updated**: 2026-05-01

---

## Problem Statement

**Problem**: Professionals lack a simple, local tool to track time spent on tasks throughout the day. Existing solutions are either over-engineered cloud apps or require manual time entry. A lightweight CLI tool that auto-tracks task transitions would reduce friction and improve time awareness.

---

## Objectives

1. Enable users to track time on tasks with zero-friction start/stop via CLI commands
2. Provide daily and period-based reports filtered by tags for productivity analysis
3. Store all data locally in SQLite for simplicity, privacy, and offline usage

---

## Scope

### In Scope

- Start, pause, and resume tasks via CLI commands
- Automatic pause of current task when starting a new one
- Tag assignment for task categorization
- Time reports: daily summary and filtered by date range/tags
- SQLite local storage
- Single-user CLI application

### Out of Scope

- Multi-user or authentication support
- Cloud sync or remote storage
- GUI or web interface
- Task dependencies or project hierarchy
- Notifications or reminders

---

## User Stories

### US-1: Start a Task

**As a** user
**I want** to start tracking time on a task by entering its name
**So that** I know exactly when I began working on it

**Acceptance Criteria**:
- [ ] AC-1: Running `start "task name"` creates a new task entry with current timestamp
- [ ] AC-2: If another task is active, it is automatically paused before the new one starts
- [ ] AC-3: User receives confirmation with task name and start time

**Priority**: High
**Complexity**: S

---

### US-2: Pause and Resume Tasks

**As a** user
**I want** to resume a previously paused task
**So that** I can continue tracking time without creating duplicates

**Acceptance Criteria**:
- [ ] AC-1: Running `resume` shows a list of paused tasks to select from
- [ ] AC-2: Resuming a task creates a new time entry linked to the same task
- [ ] AC-3: The currently active task is auto-paused when resuming another
- [ ] AC-4: Running `stop` pauses the current task without starting a new one

**Priority**: High
**Complexity**: M

---

### US-3: Tag Tasks

**As a** user
**I want** to assign tags to tasks
**So that** I can categorize and filter my work

**Acceptance Criteria**:
- [ ] AC-1: Tags can be assigned when starting a task: `start "task name" --tag dev --tag meeting`
- [ ] AC-2: Tags can be added to an existing task after creation
- [ ] AC-3: A task can have multiple tags
- [ ] AC-4: Tags are free-form text (no predefined list)

**Priority**: High
**Complexity**: S

---

### US-4: Daily Summary Report

**As a** user
**I want** to see a summary of time spent on each task today
**So that** I can review my productivity at end of day

**Acceptance Criteria**:
- [ ] AC-1: Running `report` (no args) shows today's summary
- [ ] AC-2: Report displays: task name, tags, total time, percentage of total
- [ ] AC-3: Tasks are sorted by total time (descending)
- [ ] AC-4: Shows grand total at the bottom

**Priority**: High
**Complexity**: M

---

### US-5: Filtered Reports

**As a** user
**I want** to filter reports by date range and/or tags
**So that** I can analyze time spent on specific categories over periods

**Acceptance Criteria**:
- [ ] AC-1: Filter by date range: `report --from 2026-04-01 --to 2026-04-30`
- [ ] AC-2: Filter by tag: `report --tag dev`
- [ ] AC-3: Combine filters: `report --from 2026-04-01 --tag meeting`
- [ ] AC-4: Report groups time by task with subtotals per tag when filtered

**Priority**: Medium
**Complexity**: M

---

### US-6: List Tasks

**As a** user
**I want** to see all tasks and their current status
**So that** I can know what's active, paused, or completed

**Acceptance Criteria**:
- [ ] AC-1: Running `list` shows all tasks with status (active/paused)
- [ ] AC-2: Shows tags associated with each task
- [ ] AC-3: Shows total accumulated time per task

**Priority**: Medium
**Complexity**: S

---

## Business Rules

### Core Rules

| Rule ID | Rule | Example |
|---------|------|---------|
| BR-1 | Only one task can be active at a time | Starting "task B" auto-pauses "task A" |
| BR-2 | Time is calculated from sum of all time entries for a task | Task with 3 entries of 30min each = 1h30min total |
| BR-3 | Resuming a task creates a new time entry, not modifies existing | Resume "task A" → new entry with current start time |
| BR-4 | A task with no end time on its latest entry is considered "active" | Entry {start: 10:00, end: null} → task is active |

### Validation Invariants

- **INV-1**: A task must have a non-empty name
- **INV-2**: start_time must always be set on a time entry
- **INV-3**: end_time must be >= start_time (when set)
- **INV-4**: Only one time entry across all tasks can have end_time = null at any moment

---

## Data Model

### Entities

**Task**:
- id, name, created_at
- Has many tags
- Has many time entries

**Tag**:
- id, name (unique)
- Many-to-many with tasks

**TimeEntry**:
- id, task_id, start_time, end_time (nullable)
- end_time = null means currently active

---

## User Experience

### User Persona

**Primary User**: Developer or knowledge worker tracking daily work time
- Context: Working from terminal throughout the day
- Goal: Know where time goes without leaving the CLI

### Main Flow

| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | `tracker start "code review" --tag dev` | "Started: code review [dev] at 09:00" |
| 2 | `tracker start "standup" --tag meeting` | "Paused: code review (45min). Started: standup [meeting] at 09:45" |
| 3 | `tracker resume` | Shows paused tasks, user picks "code review" |
| 4 | `tracker stop` | "Stopped: code review (30min)" |
| 5 | `tracker report` | Daily summary table |

---

## Critical E2E Test Scenarios

> LTP not applicable (local CLI). Scenarios documented for test coverage guidance.

### E2E-1: Full Task Lifecycle

**Priority**: 🔴 Critical
**Related User Story**: US-1, US-2
**Preconditions**: Empty database

**Steps**:
1. Start task "code review" with tag "dev"
2. Verify task is active with correct start time
3. Start task "standup" with tag "meeting"
4. Verify "code review" is paused and "standup" is active
5. Resume "code review"
6. Stop current task
7. Run daily report

**Expected Result**: Report shows both tasks with correct accumulated times

---

### E2E-2: Filtered Report

**Priority**: 🟡 High
**Related User Story**: US-4, US-5
**Preconditions**: Multiple tasks with different tags over multiple days

**Steps**:
1. Run report filtered by tag "dev"
2. Run report filtered by date range
3. Run report with both filters combined

**Expected Result**: Each report shows only matching tasks with correct totals

---

### E2E Test Summary

| ID | Scenario | Priority | User Story |
|----|----------|----------|------------|
| E2E-1 | Full Task Lifecycle | 🔴 Critical | US-1, US-2 |
| E2E-2 | Filtered Report | 🟡 High | US-4, US-5 |

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Command response time | < 100ms | Manual testing with 10k entries |
| Daily adoption | User runs 5+ commands/day | Self-reported usage |
| Time tracking accuracy | 100% of active time captured | Compare manual vs tracked |

---

## Non-Functional Requirements

### Performance
- All commands respond in < 100ms for databases up to 10,000 entries

### Usability
- Clear, readable terminal output with aligned columns
- Helpful error messages for invalid commands

---

## Assumptions

1. Single-user application — no concurrent access to the database
2. SQLite file stored in user's home directory or configurable path
3. Python 3.10+ available on user's system
4. Times are stored and displayed in local timezone
