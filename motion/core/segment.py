from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class MotionSegment:
    law: str
    stroke: float
    duration: float
    params: Dict[str, Any] = field(default_factory=dict)
    proportions: Any = None
