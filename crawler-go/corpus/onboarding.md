# Engineering Onboarding

Welcome to the team. Your first day is about access and environment setup.
Request your accounts through the IT portal and enable two-factor authentication.
Clone the monorepo and run the bootstrap script to install toolchains.

## Deploys

We ship from the main branch. Every merge triggers CI, and a green build is
promoted to staging automatically. Production deploys are manual and require a
second approver. Roll back with the deploy CLI if error rates spike.

## Support rotation

Engineers take a weekly on-call rotation. The on-call handles pages, triages
incidents, and writes a short postmortem for anything customer-facing.
