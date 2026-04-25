---
name: uiux-responsive-e2e
description: 'Run a full UI UX implementation and responsive E2E validation workflow. Use for frontend tasks that must pass mobile mode, iPad/tablet mode, and desktop mode checks with Playwright before completion.'
argument-hint: 'UI task, target pages/components, acceptance criteria, and critical user flow.'
user-invocable: true
disable-model-invocation: false
---

# UIUX Responsive E2E Workflow

## Outcome
Produce UI/UX changes that are implemented, validated, and signed off only after passing end-to-end checks across all required viewports.

## When To Use
- UI/UX implementation work
- Responsive bug fixes
- Layout refactors that can regress on different breakpoints
- Form and interaction improvements
- Tasks requiring strong confidence before handoff

## Required Viewports
- Mobile: 390x844
- iPad/Tablet: 768x1024
- Desktop: 1440x900

## Required Inputs
- Target page(s) or component(s)
- Intended user journey and primary task path
- Acceptance criteria
- Any edge-case constraints (locale, long text, empty state, permission state)

## Workflow
1. Understand and map the user flow.
2. Implement UI/UX changes with responsive behavior from the first edit.
3. Validate key states manually in code and UI structure:
   - Loading
   - Empty
   - Success
   - Error
4. Run E2E using Playwright with this preferred command:
   - npm run test:e2e
5. Execute checks per viewport for:
   - Layout integrity (no overlap, clipping, hidden primary actions)
   - Navigation and core task completion path
   - Forms and interactive controls
   - Readability, spacing, and touch target comfort
   - Accessibility basics (focus visibility, keyboard flow where relevant, labels clarity)
6. Capture screenshot evidence for each viewport after fixes are applied.
7. Apply fixes for any failed viewport.
8. Re-run E2E for all affected paths and viewports.

## Branching Logic
- If one viewport fails and others pass:
  - Fix the failing viewport issue.
  - Re-test all affected paths in every impacted viewport.
- If failures are cross-viewport:
  - Prioritize shared root cause (tokens, container widths, breakpoints, component constraints).
  - Re-run complete viewport matrix.
- If Playwright command is missing:
  - Check package scripts for an equivalent E2E command.
  - If no equivalent exists, report blocker and propose exact setup steps.
  - Do not mark the task complete until E2E is executable and passing.

## Completion Gates
A task is complete only when:
- Mobile passes
- iPad/Tablet passes
- Desktop passes
- Screenshot artifacts exist for all three viewports
- No unresolved critical UX issues remain in primary task flow

## Output Format
- Summary of implemented UI/UX changes
- Responsive coverage list (Mobile, iPad/Tablet, Desktop)
- E2E results by viewport: pass/fail and key findings
- Accessibility notes
- Remaining risks, blockers, or follow-up items
