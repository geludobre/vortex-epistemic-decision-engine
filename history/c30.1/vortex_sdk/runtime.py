from datetime import datetime
from .validator import validate_adapter

class AdapterRuntime:
    def __init__(self,adapter):
        validate_adapter(adapter)
        self.adapter=adapter

    def admissible_evidence(self,evidence,cutoff):
        c=datetime.fromisoformat(cutoff.replace("Z","+00:00"))
        good=[]
        for e in evidence:
            k=datetime.fromisoformat(e.known_at.replace("Z","+00:00"))
            if k>c: raise ValueError(f"known_at firewall: {e.id}")
            good.append(e)
        self.adapter.validate_evidence(good,cutoff)
        return good

    @staticmethod
    def normalize(d, allow_unknown=True):
        d=dict(d)
        if allow_unknown and "UNKNOWN" not in d: d["UNKNOWN"]=0.0
        s=sum(max(float(v),0) for v in d.values())
        return {"UNKNOWN":1.0} if s<=0 else {k:max(float(v),0)/s for k,v in d.items()}

    def run(self,evidence,cutoff,horizon=1):
        e=self.admissible_evidence(evidence,cutoff)
        S=self.adapter.estimate_state(e)
        R=self.normalize(self.adapter.representations(S))
        Z=self.normalize(self.adapter.regimes(S,R))
        O=self.normalize(self.adapter.operators(S,Z))
        F=self.adapter.future(S,R,Z,O,horizon)
        return {"S":S,"R":R,"Z":Z,"O":O,"F":F}
