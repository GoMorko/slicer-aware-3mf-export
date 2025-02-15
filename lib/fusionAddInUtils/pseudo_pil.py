import io
import builtins

from typing import (
    IO,
)

LANCZOS = '_stub'

class PseudoImage:
    def __init__(self, bin: IO[bytes]):
        self.bin = bin

    def copy(self):
        return PseudoImage(io.BytesIO(self.bin.getbuffer()))

    def resize(self, a, b):
        return self

    def save(self, path: str):
        with builtins.open(path, 'wb') as wb_file:
            wb_file.write(self.bin.getbuffer())

def open(bin: IO[bytes]):
    return PseudoImage(bin)
