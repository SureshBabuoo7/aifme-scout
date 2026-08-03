"""Allow running the package as a module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aifme_scout.cli import main

sys.exit(main())
