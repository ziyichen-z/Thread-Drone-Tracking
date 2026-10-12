import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controller import body_entry, gimbal_entry, protocol, tracking_entry


class ProtocolTests(unittest.TestCase):
    def test_body_and_gimbal_channels_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(protocol, "RUNTIME", Path(directory)):
                body_entry.velocity(0.5, -0.25, 0.1)
                gimbal_entry.look_at(132.0, 117.0)
                body = json.loads((Path(directory) / "body_command.json").read_text())
                gimbal = json.loads((Path(directory) / "gimbal_command.json").read_text())
                self.assertEqual(body["channel"], "body")
                self.assertEqual(gimbal["channel"], "gimbal")
                self.assertNotIn("target_world_m", body["command"])
                self.assertNotIn("velocity_world_mps", gimbal["command"])
                self.assertEqual(body["command"]["velocity_world_mps"]["y"], 0.1)

    def test_tracking_observation_has_frame_and_bbox_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(protocol, "RUNTIME", Path(directory)):
                tracking_entry.observation(17, 0.1, 0.2, 0.3, 0.4, confidence=0.75)
                result = json.loads((Path(directory) / "tracking_observation.json").read_text())
                self.assertEqual(result["protocol"], "tethered-tracking-observation/v1")
                self.assertEqual(result["observation"]["frame_id"], 17)
                self.assertEqual(result["observation"]["bbox_xywh_norm"]["width"], 0.3)

    def test_tracking_observation_rejects_boxes_outside_image(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(protocol, "RUNTIME", Path(directory)):
                invalid_boxes = (
                    (-0.01, 0.2, 0.3, 0.4),
                    (0.1, -0.01, 0.3, 0.4),
                    (0.8, 0.2, 0.3, 0.4),
                    (0.1, 0.8, 0.3, 0.3),
                )
                for box in invalid_boxes:
                    with self.subTest(box=box):
                        with self.assertRaisesRegex(ValueError, "clipped inside"):
                            tracking_entry.observation(17, *box)
                self.assertFalse((Path(directory) / "tracking_observation.json").exists())

    def test_latest_frame_bundle_requires_both_immutable_files(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            frames = runtime / "frames"
            frames.mkdir()
            (frames / "frame_0000000003.jpg").write_bytes(b"jpeg")
            (frames / "frame_0000000003.json").write_text("{}")
            (frames / "latest.json").write_text(json.dumps({
                "schema_version": "tethered-frame-manifest/v1",
                "frame_id": 3,
                "image_file": "frame_0000000003.jpg",
                "metadata_file": "frame_0000000003.json",
            }))
            with patch.object(protocol, "RUNTIME", runtime):
                frame_id, image, metadata = protocol.latest_frame_bundle()
            self.assertEqual(frame_id, 3)
            self.assertTrue(image.is_file())
            self.assertTrue(metadata.is_file())


if __name__ == "__main__":
    unittest.main()
