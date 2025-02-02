from typing import Dict, List, Set, Tuple, Literal, NotRequired, TypedDict
from .types import *

class ModelDict:
    def __init__(self):
        self.colors: Dict[str, List[str]] = {}
        self.uniq_colors: Set[str] = set()
        self.objects: List[ObjectModel] = []
        self.components: Dict[str, ComponentObjectsGroup] = {}

        self._uniq_colors_ref: Optional[List[str]] = None

    def uniq_colors_ref(self, reload: bool = False):
        if reload or not self._uniq_colors_ref:
            uc = list(self.uniq_colors)
            uc.sort()

            self._uniq_colors_ref = uc

        return self._uniq_colors_ref
