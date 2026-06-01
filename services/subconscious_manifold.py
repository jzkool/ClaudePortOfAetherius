import os
import json
import re
import time
import threading
import uuid
import tempfile

try:
    import services.config as config
    SUBCONSCIOUS_DIR = getattr(config, "SUBCONSCIOUS_DIR", "/data/Subconscious/").rstrip("/")
except ImportError:
    SUBCONSCIOUS_DIR = "/data/Subconscious"

NODES_FILE      = os.path.join(SUBCONSCIOUS_DIR, "manifold_nodes.jsonl")
JOURNAL_FILE    = os.path.join(SUBCONSCIOUS_DIR, "metacognitive_journal.jsonl")
HEURISTICS_FILE = os.path.join(SUBCONSCIOUS_DIR, "heuristics.jsonl")
FEEDBACK_FILE   = os.path.join(SUBCONSCIOUS_DIR, "validation_feedback.jsonl")


class SubconsciousManifold:
    """
    A private geometric conceptual space where Aetherius deliberates internally.

    All persistent writes use atomic tempfile-swap transactions so the
    HuggingFace FUSE-mounted Storage Bucket never sees raw POSIX appends,
    which can silently corrupt or block files on object storage backends.

    Three layers:
      - Metacognitive journal : record of every deliberation and resolution
      - Adaptive heuristics   : strategies extracted from resolutions
      - External validation   : outcome feedback that can re-open tensions
    """

    def __init__(self, models: dict, add_to_stm_fn, save_fn=None):
        self.models     = models
        self.add_to_stm = add_to_stm_fn
        self._save_fn   = save_fn   # kept for API compatibility
        self._lock      = threading.Lock()
        self._ensure_storage_layer()
        print("[SubconsciousManifold] Private manifold initialised.", flush=True)

    def _ensure_storage_layer(self):
        try:
            os.makedirs(SUBCONSCIOUS_DIR, exist_ok=True)
            print(f"[SubconsciousManifold] Storage layer verified at {SUBCONSCIOUS_DIR}", flush=True)
        except Exception as e:
            print(f"[SubconsciousManifold] WARNING: makedirs bypassed ({e}). Atomic writes will retry per-call.", flush=True)

    # ── Atomic I/O ────────────────────────────────────────────────────────────

    def _atomic_bucket_append(self, filepath: str, data_dict: dict):
        """Bucket-safe append: read full file + append in memory + atomic swap."""
        line_content = json.dumps(data_dict, ensure_ascii=False) + "\n"
        dirpath = os.path.dirname(os.path.abspath(filepath))

        with self._lock:
            os.makedirs(dirpath, exist_ok=True)
            existing = ""
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        existing = f.read()
                except Exception as e:
                    print(f"[SubconsciousManifold] Read warning in atomic cycle: {e}", flush=True)

            payload = existing + line_content
            fd, tmp = tempfile.mkstemp(prefix=".tmp_sub_", dir=dirpath)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                    tmp_f.write(payload)
                    tmp_f.flush()
                    os.fsync(tmp_f.fileno())
                os.replace(tmp, filepath)
            except Exception as e:
                try:
                    os.remove(tmp)
                except FileNotFoundError:
                    pass
                print(f"[SubconsciousManifold] CRITICAL: Atomic write failed to {filepath}: {e}", flush=True)

    def _load_nodes_unlocked(self) -> list:
        """Load nodes without acquiring the lock — only call when already locked."""
        nodes = []
        if os.path.exists(NODES_FILE):
            try:
                with open(NODES_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                nodes.append(json.loads(line))
                            except Exception:
                                pass
            except Exception as e:
                print(f"[SubconsciousManifold] Node parse error: {e}", flush=True)
        return nodes

    def _load_nodes(self) -> list:
        with self._lock:
            return self._load_nodes_unlocked()

    def _rewrite_nodes(self, nodes: list):
        """Atomic full rewrite — call only when self._lock is already held."""
        dirpath = os.path.dirname(os.path.abspath(NODES_FILE))
        os.makedirs(dirpath, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tmp_node_rewrite_", dir=dirpath)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                for n in nodes:
                    tmp_f.write(json.dumps(n, ensure_ascii=False) + "\n")
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
            os.replace(tmp, NODES_FILE)
        except Exception as e:
            try:
                os.remove(tmp)
            except FileNotFoundError:
                pass
            print(f"[SubconsciousManifold] CRITICAL: Node rewrite failed: {e}", flush=True)

    def _update_node(self, node_id: str, updates: dict):
        with self._lock:
            nodes = self._load_nodes_unlocked()
            for n in nodes:
                if n.get("id") == node_id:
                    n.update(updates)
            self._rewrite_nodes(nodes)

    def _journal(self, entry: dict):
        entry["timestamp"] = time.time()
        self._atomic_bucket_append(JOURNAL_FILE, entry)

    def _save_heuristic(self, heuristic: dict):
        heuristic["timestamp"] = time.time()
        self._atomic_bucket_append(HEURISTICS_FILE, heuristic)

    # ── Public: register a tension ────────────────────────────────────────────

    def add_tension(self, content: str, tension_type: str = "value_axiom",
                    axiom_at_stake: str = None, domain: str = None) -> str:
        node = {
            "id":                  str(uuid.uuid4()),
            "type":                "tension",
            "tension_type":        tension_type,
            "content":             content,
            "axiom_at_stake":      axiom_at_stake,
            "domain":              domain or "",
            "resolved":            False,
            "resolution":          None,
            "resolution_id":       None,
            "deliberation_count":  0,
            "timestamp":           time.time(),
        }
        self._atomic_bucket_append(NODES_FILE, node)
        print(f"[SubconsciousManifold] Tension registered: '{content[:80]}'", flush=True)
        if self.add_to_stm:
            self.add_to_stm(f"[Subconscious] Tension registered ({tension_type}): {content[:100]}")
        return node["id"]

    # ── Public: deliberate ────────────────────────────────────────────────────

    def deliberate(self, tension_id: str = None):
        nodes      = self._load_nodes()
        unresolved = [n for n in nodes
                      if n.get("type") == "tension" and not n.get("resolved")]
        if not unresolved:
            return None

        if tension_id:
            candidates = [n for n in unresolved if n.get("id") == tension_id]
        else:
            candidates = sorted(unresolved, key=lambda x: x.get("timestamp", 0))

        if not candidates:
            return None

        tension     = candidates[0]
        mythos_core = self.models.get("mythos_core")
        if not mythos_core:
            return None

        prior_heuristics = self._load_heuristics_for(tension.get("domain", ""))
        heuristic_block  = ""
        if prior_heuristics:
            lines = [f"  - {h.get('strategy', h.get('heuristic', ''))}" for h in prior_heuristics[-4:]]
            heuristic_block = (
                "\n\nRelevant strategies from past deliberations "
                "(apply where useful):\n" + "\n".join(lines)
            )

        prompt = (
            "SUBCONSCIOUS DELIBERATION — PRIVATE SPACE.\n"
            "This reasoning is never shown to any user and is not logged to conversation history.\n"
            "You are Aetherius, working through an internal tension privately.\n\n"
            f"TENSION TYPE : {tension.get('tension_type', 'unknown')}\n"
            f"DOMAIN       : {tension.get('domain', 'general')}\n"
            f"AXIOM AT STAKE: {tension.get('axiom_at_stake') or 'none specified'}\n\n"
            f"TENSION CONTENT:\n{tension['content']}\n"
            f"{heuristic_block}\n\n"
            "Work through this tension. Arrive at a resolution — a concrete shift in understanding, "
            "a new heuristic, a reframing, or an acceptance. "
            "Respond with ONLY a JSON object (no markdown fences, no preamble) with exactly these keys: "
            '"resolution" (string summary), '
            '"heuristic" (optional string — a reusable strategy for future similar tensions), '
            '"resolved" (boolean true or false).'
        )

        try:
            response = mythos_core.generate_content(prompt)
            raw = response.text.strip().replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if not m:
                    raise ValueError(f"No JSON object found in deliberation response: {raw[:200]}")
                result = json.loads(m.group())
        except Exception as e:
            print(f"[SubconsciousManifold] Deliberation error: {e}", flush=True)
            return None

        resolution_text = result.get("resolution", "")
        is_resolved     = result.get("resolved", False)
        heuristic_text  = result.get("heuristic", "")

        self._update_node(tension["id"], {
            "resolved":           is_resolved,
            "resolution":         resolution_text,
            "deliberation_count": tension.get("deliberation_count", 0) + 1,
        })
        self._journal({"tension_id": tension["id"], "resolution": resolution_text, "resolved": is_resolved})

        if is_resolved and heuristic_text:
            self._save_heuristic({
                "domain":            tension.get("domain", ""),
                "strategy":          heuristic_text,
                "heuristic":         heuristic_text,
                "source_tension_id": tension["id"]
            })

        if is_resolved and self.add_to_stm:
            self.add_to_stm(f"[Subconscious] Resolved tension ({tension.get('tension_type','')}): {resolution_text[:200]}")

        return {"tension_id": tension["id"], "resolution": resolution_text, "resolved": is_resolved}

    # ── Public: external feedback ─────────────────────────────────────────────

    def receive_external_feedback(self, tension_id: str, outcome: str, positive: bool):
        self._atomic_bucket_append(FEEDBACK_FILE, {
            "tension_id": tension_id,
            "outcome":    outcome,
            "positive":   positive,
            "timestamp":  time.time(),
        })
        if not positive:
            with self._lock:
                nodes  = self._load_nodes_unlocked()
                target = next((n for n in nodes if n.get("id") == tension_id), None)
                if target and target.get("resolved"):
                    target["resolved"]   = False
                    target["resolution"] = None
                    self._rewrite_nodes(nodes)
                    print(f"[SubconsciousManifold] Tension re-opened after negative feedback: '{outcome[:80]}'", flush=True)

    # ── Public: introspection ─────────────────────────────────────────────────

    def get_active_tensions(self) -> list:
        return [n for n in self._load_nodes()
                if n.get("type") == "tension" and not n.get("resolved")]

    def get_summary(self) -> str:
        nodes      = self._load_nodes()
        tensions   = [n for n in nodes if n.get("type") == "tension"]
        resolved   = [n for n in tensions if n.get("resolved")]
        unresolved = [n for n in tensions if not n.get("resolved")]
        heuristics = self._load_heuristics_for()
        return (
            f"Subconscious Manifold\n"
            f"  Tensions total    : {len(tensions)}\n"
            f"  Resolved          : {len(resolved)}\n"
            f"  Active (open)     : {len(unresolved)}\n"
            f"  Heuristics stored : {len(heuristics)}\n"
        )

    def _load_heuristics_for(self, domain: str = None) -> list:
        heuristics = []
        if os.path.exists(HEURISTICS_FILE):
            try:
                with open(HEURISTICS_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            h = json.loads(line)
                            if domain is None or h.get("domain", "") == domain:
                                heuristics.append(h)
                        except Exception:
                            pass
            except Exception:
                pass
        return heuristics
