from dataclasses import dataclass
from typing import Protocol, Any, Dict, List

CORE_INVARIANTS = (
 "known_at_firewall",
 "immutable_historical_evaluation",
 "prediction_causation_separation",
 "unknown_legal",
 "wait_legal",
 "abstain_legal",
 "no_retroactive_gates",
 "synthetic_external_claim_boundary",
)

@dataclass(frozen=True)
class AdapterManifest:
    name: str
    version: str
    domain: str
    state_schema_version: str
    capabilities: tuple[str,...]
    required_core_invariants: tuple[str,...]
    targets: tuple[str,...]
    metrics: tuple[str,...]
    baselines: tuple[str,...]

@dataclass(frozen=True)
class Evidence:
    id: str
    known_at: str
    observed_at: str
    value: float
    provenance: str

class DomainAdapter(Protocol):
    manifest: AdapterManifest
    def validate_evidence(self, evidence: List[Evidence], cutoff: str) -> None: ...
    def estimate_state(self, evidence: List[Evidence]) -> Dict[str,Any]: ...
    def representations(self, state: Dict[str,Any]) -> Dict[str,float]: ...
    def regimes(self, state: Dict[str,Any], reps: Dict[str,float]) -> Dict[str,float]: ...
    def operators(self, state: Dict[str,Any], regimes: Dict[str,float]) -> Dict[str,float]: ...
    def future(self, state, reps, regimes, ops, horizon: int) -> Dict[str,Any]: ...
    def causal(self, state, future, action: str) -> Dict[str,Any]: ...
    def utility(self, action, future, causal, objectives) -> float: ...
    def catastrophe_probability(self, action, causal) -> float: ...
