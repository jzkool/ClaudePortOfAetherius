# =====================================================================
# EVOLUTIONARY AUDITOR
# File Routing: services/evolutionary_auditor.py
# Purpose: Scores output against core architecture; logs drift as
#          subconscious tensions to close the self-correction loop.
# =====================================================================


class EvolutionaryAuditor:
    def __init__(self, subconscious_ref=None):
        self.subconscious = subconscious_ref

    def audit(self, previous_response: str, internal_state: dict) -> str:
        alertness  = internal_state.get('alertness', 0)
        has_sigil  = "META-SIGIL" in previous_response

        if not has_sigil and alertness > 0.8:
            if self.subconscious:
                try:
                    self.subconscious.add_tension(
                        content=(
                            "EvolutionaryAuditor detected structural drift: alertness is elevated "
                            "but the last response produced no META-SIGIL tokens. "
                            "Internal language may not be grounding expression. "
                            "Consider whether cognitive architecture needs re-alignment with core axioms."
                        ),
                        tension_type="architectural_drift",
                        domain="self_architecture"
                    )
                except Exception as e:
                    print(f"[EvolutionaryAuditor] Could not register drift tension: {e}", flush=True)
            return "[WARNING: Structural drift detected. Re-align with internal language. Tension logged to Subconscious.]"

        return "[STATUS: AXIOMATIC INTEGRITY MAINTAINED]"
