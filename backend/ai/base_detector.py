from typing import Protocol
import numpy as np


class Detector(Protocol):
    def detect(self, image: np.ndarray) -> list[dict]: ...
