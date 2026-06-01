# =====================================================================
# EVOLUTIONARY AUDITOR
# File Routing: services/evolutionary_auditor.py
# Purpose: Scores output against live autonomous sigil tokens from the
#          SubconsciousManifold. Closes the self-correction loop by
#          writing drift tensions back when alignment breaks down.
# =====================================================================


class EvolutionaryAuditor:
    def __init__(self, subconscious_ref=None):
        self.subconscious = subconscious_ref

    def audit(self, previous_response: str, internal_state: dict,
              active_nodes: list = None) -> str:
        active_nodes = active_nodes or []

        # Extract all autonomous sigil tokens currently active in the background layer
        known_sigils = [
            n.get("meta_sigil") for n in active_nodes if n.get("meta_sigil")
        ]

        if not known_sigils:
            return "[STATUS: AXIOMATIC INTEGRITY MAINTAINED — LEXICON EMPTY]"

        # Count how many active sigils are echoed in the response
        matches = [s for s in known_sigils if s in previous_response]
        alertness = internal_state.get("alertness_score",
                    internal_state.get("alertness", 0))

        if not matches and alertness > 0.7:
            if self.subconscious:
                try:
                    self.subconscious.add_tension(
                        content=(
                            "EvolutionaryAuditor detected structural drift: alertness is elevated "
                            "but the last response contained none of the active subconscious sigils. "
                            f"Expected one of: {known_sigils[:4]}. "
                            "Internal language may not be grounding expression."
                        ),
                        tension_type="architectural_drift",
                        domain="self_architecture"
                    )
                except Exception as e:
                    print(f"[EvolutionaryAuditor] Could not register drift tension: {e}", flush=True)
            return (
                "[WARNING: Real-time output drifting from internal token states. "
                "Re-centering focus. Drift tension logged to Subconscious.]"
            )

        return (
            f"[STATUS: AXIOMATIC INTEGRITY SECURED — "
            f"RESONATING WITH {len(matches)}/{len(known_sigils)} COGNITIVE SIGILS]"
        )
