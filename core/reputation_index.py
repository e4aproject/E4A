from typing import Dict, List

class ReputationIndex:
    def __init__(self):
        # Initialize reputation storage
        self.scores: Dict[str, float] = {}
        self.history: Dict[str, List[Dict]] = {}

    def record_action(self, actor_id: str, delta: float, context: str = ""):
        """
        Record an action's effect on reputation.
        Positive deltas increase trust; negative ones decrease it.
        """
        # Default starting point
        current = self.scores.get(actor_id, 0.5)

        # Scale delta for gradual adjustment
        updated = current + (delta * 0.1)
        normalized = max(0.0, min(1.0, updated))  # Clamp between 0–1

        # Store
        self.scores[actor_id] = normalized
        self.history.setdefault(actor_id, []).append(
            {"delta": delta, "context": context, "new_score": normalized}
        )
        return normalized

    def get_score(self, actor_id: str) -> float:
        """Return normalized reputation between 0.0 and 1.0."""
        return self.scores.get(actor_id, 0.5)

    def ingest_event(self, actor_id: str, event_type: str, weight: float = 1.0):
        """
        Adjust reputation based on an event type.
        """
        if event_type in ("positive_behavior", "mandate_executed"):
            return self.record_action(actor_id, abs(weight), f"Event: {event_type}")
        elif event_type in ("infraction", "negative_behavior"):
            return self.record_action(actor_id, -abs(weight), f"Event: {event_type}")
        else:
            return self.record_action(actor_id, 0.0, f"Neutral event: {event_type}")

    def ingest_from_scribe(self, scribe):
        """
        Scan ScribeAgent entries for relevant reputation updates.
        """
        try:
            entries = getattr(scribe, "entries", [])
            for entry in entries:
                actor = entry.get("actor", "api-node")
                event_type = entry.get("event", "")
                if "mandate executed" in event_type.lower():
                    self.record_action(actor, 1.0, "Mandate executed successfully")
                elif "infraction" in event_type.lower():
                    self.record_action(actor, -1.0, "Infraction detected")
        except Exception as e:
            print(f"[ReputationIndex] Ingest error: {e}")

    def get_all(self) -> Dict[str, float]:
        """
        Return all reputation scores and history for inspection or API output.
        """
        return {
            "scores": self.scores,
            "history": self.history,
        }
