from .contracts import CORE_INVARIANTS
class AdapterValidationError(ValueError): pass

REQUIRED_METHODS=("validate_evidence","estimate_state","representations","regimes",
                  "operators","future","causal","utility","catastrophe_probability")

def validate_adapter(adapter):
    if not hasattr(adapter,"manifest"): raise AdapterValidationError("missing manifest")
    m=adapter.manifest
    missing=[x for x in REQUIRED_METHODS if not callable(getattr(adapter,x,None))]
    if missing: raise AdapterValidationError("missing methods: "+",".join(missing))
    inv=set(m.required_core_invariants)
    absent=set(CORE_INVARIANTS)-inv
    if absent: raise AdapterValidationError("adapter does not bind all Core invariants: "+",".join(sorted(absent)))
    if not m.name or not m.version or not m.domain: raise AdapterValidationError("invalid identity")
    if not m.targets or not m.metrics or not m.baselines:
        raise AdapterValidationError("targets, metrics and baselines must be declared before evaluation")
    return True
