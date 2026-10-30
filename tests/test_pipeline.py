"""
Unit tests for Pipeline Orchestration (Stages 1-5).
"""
import io
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pipeline.scoring_pipeline import run_scoring_pipeline
from pipeline.transcription_pipeline import run_transcription_pipeline


class PipelineTestCase(unittest.TestCase):
    def test_scoring_pipeline_grammar_only(self):
        score_res = run_scoring_pipeline(
            original_transcript="She don't like apples.",
            corrected_sentence="She doesn't like apples.",
        )
        self.assertIsNotNone(score_res.grammar_score)
        self.assertIsNone(score_res.pronunciation_score)
        self.assertIsNone(score_res.fluency_score)
        self.assertEqual(score_res.overall_score, score_res.grammar_score)
        self.assertTrue(score_res.is_grammar_only)
        self.assertIn("unavailable", score_res.pronunciation_notice)

    def test_transcription_pipeline_missing_file(self):
        res = run_transcription_pipeline(Path("does_not_exist_xyz.wav"))
        self.assertFalse(res.success)
        self.assertIn("does not exist", res.error_message)


if __name__ == "__main__":
    unittest.main()
