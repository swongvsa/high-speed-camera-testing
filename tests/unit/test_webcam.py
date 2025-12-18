import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from src.camera.device import CameraInfo
from src.camera.webcam import WebcamDevice


class TestWebcamDevice(unittest.TestCase):
    def setUp(self):
        self.camera_info = CameraInfo(
            device_index=0, friendly_name="Webcam 0", port_type="USB/Webcam", source_type="webcam"
        )
        self.device = WebcamDevice(self.camera_info)

    @patch("cv2.VideoCapture")
    def test_enumerate_cameras(self, mock_vc):
        # Mock VideoCapture to return opened for index 0 and 1
        def side_effect(index):
            mock = MagicMock()
            mock.isOpened.return_value = index < 2
            return mock

        mock_vc.side_effect = side_effect

        cameras = WebcamDevice.enumerate_cameras()
        self.assertEqual(len(cameras), 2)
        self.assertEqual(cameras[0].friendly_name, "Webcam 0")
        self.assertEqual(cameras[1].friendly_name, "Webcam 1")
        self.assertEqual(cameras[0].source_type, "webcam")

    @patch("cv2.VideoCapture")
    def test_lifecycle(self, mock_vc):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            3: 640,  # CAP_PROP_FRAME_WIDTH
            4: 480,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
        }.get(prop, 0)
        mock_vc.return_value = mock_cap

        # Enter
        with self.device as dev:
            self.assertTrue(dev._initialized)
            self.assertEqual(dev._width, 640)
            self.assertEqual(dev._height, 480)

            capability = dev.get_capability()
            self.assertEqual(capability.max_width, 640)
            self.assertEqual(capability.max_height, 480)

            # Capture frames
            mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            frames = dev.capture_frames()
            frame = next(frames)
            self.assertEqual(frame.shape, (480, 640, 3))

        # Exit
        self.assertFalse(self.device._initialized)
        mock_cap.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_capture_failure(self, mock_vc):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_vc.return_value = mock_cap

        with self.device as dev:
            # First read fails, second succeeds
            mock_cap.read.side_effect = [
                (False, None),
                (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            ]

            frames = dev.capture_frames()
            frame = next(frames)
            self.assertEqual(frame.shape, (480, 640, 3))
            self.assertEqual(mock_cap.read.call_count, 2)
