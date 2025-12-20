class LCIEngine:
    def __init__(self):
        # Weights matching Whitepaper
        self.weights = {
            'accuracy': 0.30,
            'engagement': 0.25,
            'confidence': 0.20,
            'time_efficiency': 0.15,
            'consistency': 0.10
        }

    def calculate_score(self, metrics):
        score = 0.0
        for key, weight in self.weights.items():
            score += metrics.get(key, 0.5) * weight
        return min(1.0, max(0.0, score))

    def determine_tier(self, score):
        if score >= 0.70: return "High"
        if score >= 0.40: return "Medium"
        return "Low"

    # --- NEW: Adaptive Logic from useLCI.tsx ---
    def calculate_quiz_distribution(self, accuracy, confidence):
        """
        Determines question difficulty based on student metrics.
        Returns: {'Easy': count, 'Medium': count, 'Hard': count}
        """
        # Weighting: Accuracy (70%) + Confidence (30%)
        adaptive_metric = (accuracy * 0.7) + (confidence * 0.3)

        if adaptive_metric >= 0.70:
            # High Tier: Challenge them (2 Hard, 1 Medium)
            return {"Easy": 0, "Medium": 1, "Hard": 2}
        elif adaptive_metric >= 0.40:
            # Medium Tier: Balanced (1 Easy, 1 Medium, 1 Hard)
            return {"Easy": 1, "Medium": 1, "Hard": 1}
        else:
            # Low Tier: Build confidence (2 Easy, 1 Medium)
            return {"Easy": 2, "Medium": 1, "Hard": 0}

    def get_tier_color(self, tier):
        if tier == 'High': return '#64ffda' # Green/Teal
        if tier == 'Medium': return '#f59e0b' # Amber
        return '#ef4444' # Red