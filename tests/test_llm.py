"""
Unit tests for LLM Integration, Grammar Correction, Feedback, and Scoring.
External network calls to Ollama are mocked to guarantee offline reproducibility.
"""
import unittest
from unittest.mock import patch

from llm.correction import correct_sentence
from llm.exceptions import OllamaConnectionError
from llm.feedback import generate_feedback
from llm.scoring import calculate_overall_score, compute_grammar_score


class LLMScoringTestCase(unittest.TestCase):
    def test_grammar_score_identical_sentence(self):
        score = compute_grammar_score("I went to school yesterday.", "I went to school yesterday.")
        self.assertEqual(score, 100.0)

    def test_grammar_score_minor_case_and_punctuation(self):
        score = compute_grammar_score("i went to school yesterday", "I went to school yesterday.")
        self.assertEqual(score, 100.0)

    def test_grammar_score_grammatical_deviation(self):
        score = compute_grammar_score("I goes to market", "I go to the market.")
        self.assertGreaterEqual(score, 0.0)
        self.assertLess(score, 100.0)

    def test_overall_score_unconfigured_pronunciation(self):
        # When pronunciation scoring is disabled, overall score is based strictly on available metrics
        res = calculate_overall_score(grammar_score=85.0, pronunciation_score=None)
        self.assertEqual(res["overall_score"], 85.0)
        self.assertIsNone(res["pronunciation_score"])
        self.assertTrue(res["is_grammar_only"])
        self.assertIn("unavailable", res["pronunciation_notice"])


class LLMCorrectionAndFeedbackTestCase(unittest.TestCase):
    def test_rule_based_fallback_on_offline(self):
        # Force rule_based provider
        result = correct_sentence("yesterday i go to store", provider="rule_based")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("store", result["corrected"].lower())
        self.assertEqual(result["provider_used"], "fallback_rules")

    def test_ollama_mocked_success(self):
        try:
            import requests
        except ImportError:
            self.skipTest("requests library not installed yet")
        with patch("llm.model.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "response": '{"corrected": "I went to the store yesterday.", "explanation": "Changed verb tense to past simple.", "changed": true}'
            }
            result = correct_sentence("yesterday I go store", provider="ollama")
            self.assertEqual(result["corrected"], "I went to the store yesterday.")
            self.assertEqual(result["status"], "SUCCESS")

    def test_ollama_connection_failure_falls_back_gracefully(self):
        try:
            import requests
        except ImportError:
            self.skipTest("requests library not installed yet")
        with patch("llm.model.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            result = correct_sentence("he go to school", provider="ollama")
            self.assertIn(result["status"], ["SUCCESS", "NO_CHANGE"])
            self.assertEqual(result["provider_used"], "fallback_rules")

    def test_feedback_generator_identical_sentence(self):
        feedback = generate_feedback("The weather is nice today.", "The weather is nice today.")
        self.assertIn("accurate", feedback.lower())

    def test_feedback_generator_rule_based(self):
        feedback = generate_feedback("He go home", "He goes home.")
        self.assertTrue(len(feedback) > 10)
        self.assertIn("•", feedback)


if __name__ == "__main__":
    unittest.main()
