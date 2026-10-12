from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import cv2

from controller.trackers import create_csrt_backend


def main() -> None:
    tracker = create_csrt_backend(cv2)
    constructor = (
        "cv2.TrackerCSRT_create"
        if callable(getattr(cv2, "TrackerCSRT_create", None))
        else "cv2.legacy.TrackerCSRT_create"
    )
    print(
        json.dumps(
            {
                "opencv_version": cv2.__version__,
                "constructor": constructor,
                "tracker_type": type(tracker).__name__,
                "environment": str(Path(sys.prefix).resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
