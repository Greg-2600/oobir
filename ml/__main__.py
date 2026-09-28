"""Allow ``python -m ml ...`` to act as the CLI."""

import sys

from .train import _cli

if __name__ == "__main__":
    _cli(sys.argv[1:])
