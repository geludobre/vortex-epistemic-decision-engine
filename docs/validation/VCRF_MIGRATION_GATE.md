# VCRF Migration Gate

**Status:** BLOCKED ON CANONICAL SOURCE ARTIFACT

VCRF is named in the Vortex consolidation plan, but no canonical VCRF source file or unambiguous semantic definition was located in the accessible default branches during this consolidation loop.

The public SSOT must not reconstruct VCRF from memory or infer an expansion for the acronym.

## Required before migration

1. identify the canonical source artifact and repository/commit or immutable archive hash;
2. record the original VCRF name, semantics, inputs, outputs, invariants, and version;
3. preserve any historical FAIL/INCONCLUSIVE results associated with it;
4. migrate the source unchanged first, or document every transformation explicitly;
5. add contract and falsification tests before VCRF is wired into the Decision API;
6. distinguish historical/controlled evidence from prospective evidence.

Until those conditions are met, the public reference engine remains deliberately conservative and returns non-action outcomes rather than fabricating VCRF behavior.
