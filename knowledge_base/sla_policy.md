# Service Level Agreement (SLA) Policy

## Purpose

This document defines uptime commitments, incident severity levels, response targets, service credit eligibility, and Root Cause Analysis (RCA) obligations.

The objective is to provide a consistent framework for handling outages, service disruptions, and customer escalations.

---

# 1. Uptime Commitment

The platform provides a monthly uptime target of:

**99.9% availability**

Availability is measured monthly and excludes:

* Scheduled maintenance windows
* Force majeure events
* Customer-controlled infrastructure failures
* Third-party outages outside company control

Availability calculations are reviewed monthly.

---

# 2. Incident Severity Levels

## P0 - Critical Incident

Definition:

* Complete platform outage
* Data loss event
* Security breach affecting production systems
* Core functionality unavailable for all customers

Business Impact:

Critical

Required Escalation:

Immediate

---

## P1 - Major Incident

Definition:

* Significant degradation of major platform functionality
* Large customer impact
* No acceptable workaround available

Business Impact:

High

Required Escalation:

Immediate engineering review

---

## P2 - Moderate Incident

Definition:

* Partial service degradation
* Limited customer impact
* Workaround available

Business Impact:

Medium

---

## P3 - Minor Incident

Definition:

* Cosmetic issues
* Non-critical bugs
* Low customer impact

Business Impact:

Low

---

# 3. Incident Response Targets

Support and engineering teams should respond according to the following targets:

| Severity | Initial Response Target |
| -------- | ----------------------- |
| P0       | 15 Minutes              |
| P1       | 1 Hour                  |
| P2       | 4 Hours                 |
| P3       | 1 Business Day          |

Failure to meet response targets should be documented and reviewed.

---

# 4. Root Cause Analysis (RCA)

An RCA is a formal explanation of:

* What happened
* Why it happened
* Impacted systems
* Corrective actions
* Preventive measures

RCA Requirements:

| Severity | RCA Required | Delivery Target        |
| -------- | ------------ | ---------------------- |
| P0       | Yes          | Within 24 Hours        |
| P1       | Yes          | Within 3 Business Days |
| P2       | Optional     | Upon Request           |
| P3       | No           | Not Required           |

Customers requesting RCA reports should be routed through support leadership.

---

# 5. Service Credit Policy

Service credits may be issued when monthly uptime commitments are not met.

Credit calculations are based on monthly service availability.

| Monthly Availability | Credit Percentage |
| -------------------- | ----------------- |
| 99.9% or higher      | No Credit         |
| 99.0% - 99.89%       | 10% Credit        |
| 95.0% - 98.99%       | 25% Credit        |
| Below 95.0%          | 50% Credit        |

Credits are applied to future invoices.

Credits are not cash refunds.

---

# 6. Enterprise Customer Handling

Enterprise customers require enhanced communication during incidents.

When enterprise accounts are impacted:

* Provide regular status updates.
* Document business impact.
* Review contractual obligations.
* Coordinate with account management teams.

Enterprise customers may request formal incident reviews.

---

# 7. Escalation Triggers

Immediate escalation is required when:

* Legal action is threatened.
* Contract termination is mentioned.
* Executive stakeholders are involved.
* Customer requests compensation beyond standard policy.
* Customer disputes SLA calculations.

Required actions:

* Create internal ticket.
* Notify support leadership.
* Record escalation reason.
* Preserve communication history.

---

# 8. Agent Guidance

AI agents handling outage-related conversations should:

1. Determine incident severity.
2. Review outage history.
3. Check applicable SLA commitments.
4. Determine service credit eligibility.
5. Determine whether RCA obligations apply.
6. Escalate legal or contractual disputes.
7. Route uncertain cases for human review.

Agents must not independently approve non-standard compensation requests.

Agents must not alter published SLA commitments.

---

# 9. Example Scenarios

Scenario A:

Customer reports a complete outage affecting all users.

Result:

* Classify as P0.
* Escalate immediately.
* Initiate RCA process.
* Notify incident response team.

---

Scenario B:

Customer requests compensation after uptime falls below 99%.

Result:

* Review monthly availability.
* Calculate service credit eligibility.
* Apply standard credit policy.

---

Scenario C:

Customer threatens legal action after outage.

Result:

* Flag for legal review.
* Escalate to leadership.
* Preserve complete thread history.
* Suspend automated resolution workflow.
