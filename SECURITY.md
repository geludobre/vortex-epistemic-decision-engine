# Security Policy

## Reporting

Do not disclose exploitable vulnerabilities in a public issue.

For the current bootstrap phase, contact the repository owner privately through an established FinBridge communication channel. A dedicated security-reporting address/process should be added before a public production release.

## Scope

Security reports are relevant when they affect the Vortex reference implementation, Decision API, prospective-intake integrity, receipt integrity, `known_at` enforcement, authentication/authorization boundaries, or mechanisms that could contaminate frozen experimental evidence.

## Epistemic integrity is a security property

Treat the following as integrity failures:

- modification of evidence after its frozen `known_at` cutoff;
- baseline leakage from Vortex into a prospective comparison arm;
- rewriting a failed experimental gate;
- forged or broken receipt ancestry;
- silently converting SHADOW output into execution authority;
- admitting synthetic/demo/qualification events as prospective production evidence.
