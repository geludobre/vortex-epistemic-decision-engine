from .contracts import VortexState
from datetime import datetime

class VortexEngine:
    UNCERTAINTIES=("parameter","representation","regime","operator","causal","predictive","decision","unknown")

    def __init__(self, adapter, ledger, catastrophe_tau=0.05):
        self.adapter=adapter
        self.ledger=ledger
        self.tau=catastrophe_tau

    @staticmethod
    def _check_known_at(evidence, cutoff):
        c=datetime.fromisoformat(cutoff.replace("Z","+00:00"))
        for e in evidence:
            k=datetime.fromisoformat(e.known_at.replace("Z","+00:00"))
            if k>c: raise ValueError(f"anti-leakage violation: {e.id} known after cutoff")

    @staticmethod
    def _normalize(d, legal_unknown=True):
        d=dict(d)
        if legal_unknown and "UNKNOWN" not in d: d["UNKNOWN"]=0.0
        s=sum(max(0.0,float(v)) for v in d.values())
        if s<=0:
            return {"UNKNOWN":1.0}
        return {k:max(0.0,float(v))/s for k,v in d.items()}

    def run(self, evidence, cutoff, objectives, actions):
        self._check_known_at(evidence,cutoff)
        self.adapter.validate_evidence(evidence,cutoff)
        S=self.adapter.estimate_state(evidence)
        R=self._normalize(self.adapter.representations(S))
        Z=self._normalize(self.adapter.regimes(S,R))
        O=self._normalize(self.adapter.operators(S,Z))
        G=self.adapter.graph(S)
        F=self.adapter.future(S,R,Z,O)

        U={k:0.0 for k in self.UNCERTAINTIES}
        U.update(F.get("uncertainty",{}))
        J=dict(objectives)

        decisions=[]
        for a in actions:
            causal=self.adapter.causal(S,F,a)
            pcat=float(self.adapter.catastrophe_probability(a,causal))
            util=float(self.adapter.utility(a,F,causal))
            decisions.append({"action":a,"utility":util,"p_catastrophe":pcat,"admissible":pcat<=self.tau})
        decisions += [
          {"action":"wait","utility":0.0,"p_catastrophe":0.0,"admissible":True},
          {"action":"abstain","utility":-0.01,"p_catastrophe":0.0,"admissible":True}
        ]
        admissible=[d for d in decisions if d["admissible"]]
        choice=max(admissible,key=lambda x:x["utility"])

        state=VortexState(list(evidence),S,R,Z,O,G,F,U,J,{"cutoff":cutoff})
        frozen={
          "adapter":{"name":self.adapter.name,"version":self.adapter.version},
          "cutoff":cutoff,"state":{
            "S":S,"R":R,"Z":Z,"O":O,"G":G,"F":F,"U":U,"J":J
          },"decision_set":decisions,"recommended":choice
        }
        receipt=self.ledger.freeze("forecast_decision",frozen)
        return state,choice,receipt
