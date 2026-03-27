"""
Hello World domain — minimal 2-category, 3-action, 2-factor copilot.
The simplest possible DomainConfig implementation.
"""
CATEGORIES = ["low_risk", "high_risk"]
ACTIONS    = ["approve", "review", "reject"]
FACTORS    = ["score_a", "score_b"]


class HelloWorldConfig:
    categories    = CATEGORIES
    actions       = ACTIONS
    n_factors     = 2
    penalty_ratio = 5.0
    eta_confirm   = 0.05
    eta_override  = 0.01
    d_max         = 0.20
    tau           = 0.1

    @classmethod
    def get_initial_centroids(cls) -> dict:
        return {cat: {act: [0.5, 0.5] for act in cls.actions}
                for cat in cls.categories}

    @classmethod
    def get_sigma_profile(cls) -> list[float]:
        return [0.15, 0.15]

    @classmethod
    def get_category_index(cls, category: str) -> int:
        return cls.categories.index(category)

    @classmethod
    def get_action_index(cls, action: str) -> int:
        return cls.actions.index(action)
