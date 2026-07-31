from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class MotionSegment:
    law: str
    stroke: float
    duration: float
    params: Dict[str, Any] = field(default_factory=dict)
    proportions: Any = None

    def __post_init__(self):
        if self.proportions is not None and "proportions" not in self.params:
            self.params["proportions"] = self.proportions
        elif "proportions" in self.params and self.proportions is None:
            self.proportions = self.params["proportions"]
