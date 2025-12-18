import unittest
from unittest.mock import MagicMock, patch

from src.camera.device import CameraDevice, CameraInfo
from src.camera.init import enumerate_all_cameras, initialize_camera
from src.camera.webcam import WebcamDevice


class TestCameraInit(unittest.TestCase):
    @patch("src.camera.device.CameraDevice.enumerate_cameras")
    @patch("src.camera.webcam.WebcamDevice.enumerate_cameras")
    def test_enumerate_all_cameras(self, mock_web_enum, mock_mv_enum):
        # Mock MindVision cameras
        mock_mv_enum.return_value = [CameraInfo(0, "MV-Cam", "GigE", "mindvision")]
        # Mock Webcams
        mock_web_enum.return_value = [CameraInfo(1, "Webcam 0", "USB", "webcam")]

        cameras = enumerate_all_cameras()
        self.assertEqual(len(cameras), 2)
        self.assertEqual(cameras[0].friendly_name, "MV-Cam")
        self.assertEqual(cameras[1].friendly_name, "Webcam 0")

    @patch("src.camera.device.CameraDevice.__enter__")
    @patch("src.camera.device.CameraDevice.get_capability")
    def test_initialize_mindvision(self, mock_cap, mock_enter):
        mock_cap.return_value = MagicMock(max_width=1280, max_height=720)

        info = CameraInfo(0, "MV-Cam", "GigE", "mindvision")
        camera, error = initialize_camera(selected_info=info)

        self.assertIsNone(error)
        self.assertIsInstance(camera, CameraDevice)
        mock_enter.assert_called_once()

    @patch("src.camera.webcam.WebcamDevice.__enter__")
    @patch("src.camera.webcam.WebcamDevice.get_capability")
    def test_initialize_webcam(self, mock_cap, mock_enter):
        mock_cap.return_value = MagicMock(max_width=640, max_height=480)

        info = CameraInfo(1, "Webcam 0", "USB", "webcam")
        camera, error = initialize_camera(selected_info=info)

        self.assertIsNone(error)
        self.assertIsInstance(camera, WebcamDevice)
        mock_enter.assert_called_once()
