"""Built-in seed documents + an eval set, so the engine is useful and testable
with no crawler and no services running."""

SEED_DOCS = {
    "hr/pto.md": (
        "Employees accrue paid time off every month and can carry a limited "
        "balance into the next year.\n\n"
        "To request time off, open the HR portal and submit a leave request with "
        "your dates. Your manager approves or declines within two business days.\n\n"
        "Sick leave is separate from vacation and does not require advance notice. "
        "Notify your manager as early as you can on the day."
    ),
    "eng/deploys.md": (
        "We ship from the main branch. Every merge triggers continuous "
        "integration, and a green build is promoted to staging automatically.\n\n"
        "Production deploys are manual and require a second approver. Roll back "
        "with the deploy CLI if error rates spike."
    ),
    "eng/oncall.md": (
        "Engineers take a weekly on-call rotation. The on-call engineer handles "
        "pages, triages incidents, and writes a short postmortem for anything "
        "customer facing.\n\n"
        "Escalate to the incident commander when an outage affects many customers."
    ),
}

# (question, terms we expect a good answer to contain) — used by /eval.
EVAL_SET = [
    {"question": "how do I request time off?", "expect": ["hr", "portal", "leave"]},
    {"question": "who approves production deploys?", "expect": ["approver", "manual"]},
    {"question": "what does the on-call engineer do?", "expect": ["pages", "incidents"]},
]
