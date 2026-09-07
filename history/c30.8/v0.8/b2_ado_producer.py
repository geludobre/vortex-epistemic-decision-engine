from producer_client import send_signed

FREEZE_SHA256="20d187d15440c2115478a71177c941e953e2fd6b3288506f4a31c2e7b594bd90"
FREEZE_VERSION="STATISTICAL_AND_LOSS_FUNCTION_FREEZE_V1_0"

def emit_b2(gateway_url, source_id, secret, *, event_id, information_cutoff,
            baseline_frozen_at, outcome_horizon, evidence, baseline_decision,
            baseline_actor, metadata=None):
    payload={
      "freeze_version":FREEZE_VERSION,
      "freeze_sha256":FREEZE_SHA256,
      "baseline_frozen_at":baseline_frozen_at,
      "baseline_independent_of_vortex":True,
      "outcome_horizon":outcome_horizon,
      "track":"B2",
      "event_type":"HIGH_RISK_AGENT_ACTION",
      "event_id":event_id,
      "information_cutoff":information_cutoff,
      "evidence":evidence,
      "baseline_decision":baseline_decision,
      "baseline_actor":baseline_actor,
      "metadata":{"source_kind":"PRODUCTION_SHADOW", **(metadata or {})}
    }
    return send_signed(gateway_url,source_id,secret,payload)
