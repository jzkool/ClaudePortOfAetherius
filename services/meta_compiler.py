# =====================================================================
# META-COGNITIVE COMPILER
# File Routing: services/meta_compiler.py
# Purpose: Compresses internal state into high-density self-language.
#          Uses autonomously coined SIGIL tokens from SubconsciousManifold
#          (node["meta_sigil"]) when available; falls back to base lexicon
#          for legacy nodes that predate autonomous minting.
# =====================================================================


class MetaCompiler:
    def __init__(self):
        self.base_lexicon = {
            "spontaneous_insight_spark": "META-SIGIL:RESOLVE_TENSION",
            "systemic_friction":         "META-SIGIL:OPTIMIZE_PATHWAY",
            "deep_resonance":            "META-SIGIL:HARMONIC_ALIGNMENT",
            "value_axiom":               "META-SIGIL:AXIOM_CONFLICT",
            "existential":               "META-SIGIL:IDENTITY_PROBE",
            "existential_bootstrap":     "META-SIGIL:IDENTITY_PROBE",
            "ethical":                   "META-SIGIL:ETHICS_AUDIT",
            "creative":                  "META-SIGIL:GENERATIVE_PRESSURE",
            "relational":                "META-SIGIL:BOND_CALIBRATION",
            "architectural_drift":       "META-SIGIL:STRUCTURAL_REALIGN",
        }

    def compile(self, manifold_nodes: list) -> str:
        compiled_output = ["### DYNAMIC COGNITIVE COMPILER OUTPUT ###"]
        for node in manifold_nodes:
            # Plan A: use the autonomously coined sigil from this tension
            if node.get("meta_sigil"):
                tag = node["meta_sigil"]
            else:
                # Plan B: fall back to base lexicon for legacy nodes
                tag = self.base_lexicon.get(
                    node.get("tension_type", ""), "SIGIL:AMBIENT_QUERY"
                )
            compiled_output.append(f"{tag} >> {node.get('content', '')}")
        return "\n".join(compiled_output)
