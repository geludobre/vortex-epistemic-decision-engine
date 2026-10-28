from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol

@dataclass(frozen=True)
class Evidence:
    id: str
    observed_at: str
    known_at: str
    value: float
    provenance: str
    status: str = "observed"

@dataclass
class VortexState:
    E: List[Evidence]
    S: Dict[str, Any]
    R: Dict[str, float]
    Z: Dict[str, float]
    O: Dict[str, float]
    G: Dict[str, Any]
    F: Dict[str, Any]
    U: Dict[str, float]
    J: Dict[str, Any]
    M: Dict[str, Any]

class DomainAdapter(Protocol):
    name: str
    version: str
    def validate_evidence(self, evidence: List[Evidence], cutoff: str) -> None: ...
    def estimate_state(self, evidence: List[Evidence]) -> Dict[str, Any]: ...
    def representations(self, state: Dict[str, Any]) -> Dict[str, float]: ...
    def regimes(self, state: Dict[str, Any], representations: Dict[str,float]) -> Dict[str,float]: ...
    def operators(self, state: Dict[str,Any], regimes: Dict[str,float]) -> Dict[str,float]: ...
    def graph(self, state: Dict[str,Any]) -> Dict[str,Any]: ...
    def future(self, state, reps, regimes, ops) -> Dict[str,Any]: ...
    def causal(self, state, future, action: str) -> Dict[str,Any]: ...
    def utility(self, action: str, future: Dict[str,Any], causal: Dict[str,Any]) -> float: ...
    def catastrophe_probability(self, action: str, causal: Dict[str,Any]) -> float: ...
