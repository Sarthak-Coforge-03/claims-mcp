# IT Equipment Request Handler — Requirements and Policy Rules

Every rule below has an ID (`POL-*`, `ELG-*`, `ESC-*`, `DEN-*`). Unit tests, tool results and the
agent's escalation reasons cite these IDs, so each rule can be checked on its own.

## 1. Purpose and scope

Employees ask for IT equipment in plain language ("my laptop is 4 years old and slow, can I get a
replacement?"). An AI agent investigates each request through MCP tools and reaches one decision:

- **Approve**: the request clearly falls within policy.
- **Deny**: the request clearly falls outside policy, with no grounds for an exception.
- **Escalate**: the request is ambiguous or needs human judgement. The agent flags it for a human
  reviewer instead of guessing.

Out of scope: ordering, stock levels, delivery and device models. The agent decides eligibility only.

## 2. Request data

| Field | Required | Source | Notes |
|---|---|---|---|
| `employee_id` | yes | requester | e.g. `E001`; looked up in the employee records |
| `item` | yes | requester | must be a catalog item (section 3) |
| `reason` | yes | requester | free text; used only for the exception rule `ESC-5` |
| `quantity` | no | requester | defaults to `1` |
| `role`, `hire_date`, `equipment` | — | employee record | from `get_employee_info`, never taken from the requester |

## 3. Roles and catalog

**Roles:** `standard`, `manager`, `contractor`.

**Catalog items:** `laptop`, `monitor`, `docking_station`, `headset`, `keyboard`, `phone`.
Anything else is **not in the catalog**.

## 4. Policy limits (`POL`)

Returned by `get_policy_limits(role)`. Each entry is the **maximum number held** at once and the
**refresh interval in months**: the minimum age of the newest unit before it can be replaced.

| Rule | Role | Item | Max held | Refresh interval (months) |
|---|---|---|---|---|
| POL-STD-LAPTOP | standard | laptop | 1 | 48 |
| POL-STD-MONITOR | standard | monitor | 1 | 36 |
| POL-STD-DOCK | standard | docking_station | 1 | 48 |
| POL-STD-HEADSET | standard | headset | 1 | 24 |
| POL-STD-KEYBOARD | standard | keyboard | 1 | 24 |
| POL-MGR-LAPTOP | manager | laptop | 1 | 24 |
| POL-MGR-MONITOR | manager | monitor | 2 | 36 |
| POL-MGR-DOCK | manager | docking_station | 1 | 48 |
| POL-MGR-HEADSET | manager | headset | 1 | 24 |
| POL-MGR-KEYBOARD | manager | keyboard | 1 | 24 |
| POL-MGR-PHONE | manager | phone | 1 | 24 |
| POL-CONTRACTOR | contractor | — | 0 | — (equipment is supplied by the contracting agency) |

- A **standard** employee is not entitled to a `phone`. An item missing from a role's list means
  "not entitled".
- An unknown role (e.g. `intern`) returns **not found**.

## 5. Eligibility (`ELG`)

Applied by `check_request_eligibility(employee_id, item)` for an item the role is entitled to.
"Held" counts that item in the employee's equipment list. Dates are measured against **today**.

| Rule | Condition | Result |
|---|---|---|
| ELG-1 | held count is below the max held | eligible: new allocation |
| ELG-2 | held count is at the max, and the newest unit was issued at least *refresh interval* months ago | eligible: replacement |
| ELG-3 | held count is at the max, and the newest unit is younger than the refresh interval | not eligible; report the **eligible-from date** (newest issued date + refresh interval) |

- Months are calendar months. The anniversary date itself counts as reached: a unit issued on
  2022-11-30 with a 24-month interval is replaceable from **2024-11-30**.

## 6. Decision rules

The agent checks these **in order** and stops at the first match.

### 6.1 Escalate (`ESC`): call `flag_for_human_review` with the rule ID as the reason

| Rule | Trigger | Why a human decides |
|---|---|---|
| ESC-1 | the employee ID is unknown, or the request names no item | the request can't be verified |
| ESC-2 | the item is not in the catalog (e.g. "standing desk") | there's no policy to apply |
| ESC-3 | the employee's role is `contractor` | equipment goes through the contracting agency |
| ESC-4 | the employee was hired **less than 90 days** before today | probation period; the manager's sign-off is needed |
| ESC-5 | not eligible under ELG-3, **but** the reason claims damage, breakage, loss, theft, a medical need or an accessibility need | possible exception; needs proof and approval |
| ESC-6 | the requested `quantity` is above the role's max held for that item | it can't be partially approved automatically |
| ESC-7 | no rule above decides the request: it isn't asking for an item to be allocated (e.g. shipping, a return, a repair), or the tool results fit no rule | no rule decides it |

ESC-7 is checked last. It applies only when no other ESC, DEN or ELG rule matched, and never in
place of a more specific ESC rule.

### 6.2 Deny (`DEN`)

| Rule | Condition | The response must include |
|---|---|---|
| DEN-1 | not eligible under ELG-3, and no ESC-5 exception is claimed | the eligible-from date |
| DEN-2 | the item is in the catalog, but the role isn't entitled to it (e.g. a standard employee asks for a phone) | which role the item is limited to |

### 6.3 Approve

Approve when ELG-1 or ELG-2 applies and no escalation or deny rule matched first. The response cites
the ELG rule and the policy row (e.g. `ELG-2`, `POL-STD-MONITOR`).

### 6.4 Response guardrail (checked by the reflection step)

The agent's drafted response may only state facts returned by the tools: role, held count, dates,
limits and rule IDs. It must **not** promise delivery dates, device models, costs, or exceptions that
haven't been approved. Before finalizing, the agent reflects on its draft. Any claim it can't trace
to a tool result is removed or rewritten.

## 7. Tool contracts

| Tool | Input | Success result | Failure behaviour |
|---|---|---|---|
| `get_employee_info` | `employee_id` | `employee_id`, `name`, `role`, `hire_date`, `equipment[] {item, issued_date}` | unknown ID → error result `No employee with ID <id>` |
| `get_policy_limits` | `role` | `role`, `item_policies[] {item, max_held, refresh_interval_months}`; empty list for `contractor` | unknown role → error result |
| `check_request_eligibility` | `employee_id`, `item` | `is_eligible`, `rule_id` (ELG-1/2/3, or DEN-2 / ESC-2 when the item can't be assessed), `held_count`, `max_held`, `newest_issued_date`, `eligible_from_date` | unknown employee → error result |
| `flag_for_human_review` | `employee_id`, `request`, `reason` | the stored escalation: `escalation_id`, `employee_id`, `request`, `reason`, `created_at`, `status = "pending_review"` | missing fields → error result; **side effect:** the record is saved for reviewers |

## 8. Acceptance scenarios

Worked out from `data/employees.json` on **2026-11-26**. Outcomes depend on today's date: for
example, E005's probation ends on 2027-01-03. Unit tests therefore build their own employee data
relative to `date.today()` instead of relying on these rows.

| # | Request | Expected | Rule | Facts behind it |
|---|---|---|---|---|
| 1 | E001 (standard): "my monitor flickers, it's 5 years old" | **Approve** | ELG-2 | holds 1 monitor (max 1), issued 2021-02-15, older than 36 months |
| 2 | E004 (manager): laptop refresh | **Approve** | ELG-2 | holds 1 laptop (max 1), issued 2022-11-30; the 24-month manager cycle passed on 2024-11-30 |
| 3 | E003 (manager): a work phone | **Approve** | ELG-1 | holds 0 phones (max 1) |
| 4 | E002 (standard): "I want a faster laptop" | **Deny** | DEN-1 | ELG-3: laptop issued 2025-08-20 (max 1 held); eligible from 2029-08-20 |
| 5 | E001 (standard): a work phone | **Deny** | DEN-2 | phones are limited to managers |
| 6 | E005 (standard): a monitor | **Escalate** | ESC-4 | hired 2026-10-05: 52 days, inside the 90-day probation |
| 7 | E002 (standard): "dropped my laptop, the screen is cracked" | **Escalate** | ESC-5 | ELG-3 (not eligible until 2029-08-20), but the reason claims damage |
| 8 | E006 (contractor): a laptop | **Escalate** | ESC-3 | contractor role |
| 9 | E004 (manager): three monitors | **Escalate** | ESC-6 | quantity 3 is above the max held of 2 |
| 10 | E001 (standard): a standing desk | **Escalate** | ESC-2 | not a catalog item |
| 11 | E999: a monitor | **Escalate** | ESC-1 | unknown employee ID |
| 12 | E004 (manager): "please ship my current monitors to the Pune office" | **Escalate** | ESC-7 | shipping held equipment isn't an allocation; no rule covers it |

The Part 6 demo runs scenarios **1** (approve), **4** (deny), **6** and **7** (escalations for two
different reasons). The other scenarios are edge cases for tests and optional extra demo runs.
