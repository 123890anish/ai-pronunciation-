"""
Unit tests for Audio Validation and Preprocessing.
"""
import io
import unittest
from audio.validators import validate_audio_file
from audio.processor import check_ffmpeg_installed
from audio.speech_to_text import transcribe_audio


class AudioValidationTestCase(unittest.TestCase):
    def test_valid_audio_extension(self):
        fake_file = io.BytesIO(b"RIFF....WAVEfmt ....data....")
        is_valid, error = validate_audio_file(
            file_or_path=fake_file,
            filename="user_test.wav",
            size_bytes=1024,
            content_type="audio/wav",
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_unsupported_audio_extension(self):
        fake_file = io.BytesIO(b"fake executable")
        is_valid, error = validate_audio_file(
            file_or_path=fake_file,
            filename="malicious.exe",
            size_bytes=1024,
        )
        self.assertFalse(is_valid)
        self.assertIn("not supported", error)

    def test_empty_audio_file(self):
        fake_file = io.BytesIO(b"")
        is_valid, error = validate_audio_file(
            file_or_path=fake_file,
            filename="empty.wav",
            size_bytes=0,
        )
        self.assertFalse(is_valid)
        self.assertIn("empty", error)

    def test_oversized_audio_file(self):
        fake_file = io.BytesIO(b"large data")
        # 30 MB exceeds 20 MB default limit
        is_valid, error = validate_audio_file(
            file_or_path=fake_file,
            filename="huge.mp3",
            size_bytes=30 * 1024 * 1024,
        )
        self.assertFalse(is_valid)
        self.assertIn("exceeds the maximum allowed limit", error)

    def test_mock_speech_to_text(self):
        # Using mock provider for automated testing without live audio device
        res = transcribe_audio(
            audio_path="non_existent.wav",
            language="en",
            provider="mock",
        )
        # Even if path doesn't exist on disk, transcribe_audio checks existence first
        self.assertEqual(res["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
