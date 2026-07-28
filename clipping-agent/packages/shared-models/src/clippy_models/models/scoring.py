from pydantic import BaseModel


class ScoringWeights(BaseModel):
    virality: float = 1.0
    retention: float = 0.9
    hook: float = 0.8
    emotion: float = 0.7
    shareability: float = 0.6
    educational: float = 0.4


class LearningInsight(BaseModel):
    signal_type: str
    weight_before: float
    weight_after: float
    delta: float
    confidence: float
