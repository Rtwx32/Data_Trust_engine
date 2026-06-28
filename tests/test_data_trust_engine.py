import tempfile
import unittest
from pathlib import Path

from data_trust_engine import DataTrustEngine


class DataTrustEngineTests(unittest.TestCase):
    def test_returns_score_layers_and_arabic_explanations(self):
        engine = DataTrustEngine(memory_path=str(Path(tempfile.gettempdir()) / "dt_memory_a.json"))
        result = engine.evaluate_record(
            {
                "respondent_id": "u1",
                "age": 31,
                "education": "Computer Science",
                "job_title": "Software Engineer",
                "income": 14500,
                "response_time_seconds": 120,
                "employment_status": "employed",
                "city": "Riyadh",
                "likert_answers": [3, 4, 3, 5],
            }
        )

        self.assertTrue(0 <= result["trust_score"] <= 100)
        self.assertEqual(11, len(result["layer_scores"]))
        self.assertEqual(11, len(result["explanations_ar"]))
        self.assertTrue(any("فحص" in msg or "تحليل" in msg for msg in result["explanations_ar"]))

    def test_known_local_pivot_is_not_flagged_as_anomaly(self):
        engine = DataTrustEngine(memory_path=str(Path(tempfile.gettempdir()) / "dt_memory_b.json"))
        result = engine.evaluate_record(
            {
                "respondent_id": "u2",
                "age": 29,
                "education": "Islamic Studies",
                "job_title": "Software Engineer",
                "income": 12000,
                "response_time_seconds": 95,
                "employment_status": "employed",
                "city": "Jeddah",
                "likert_answers": [2, 3, 4, 2],
            }
        )

        self.assertGreaterEqual(result["layer_scores"]["semantic_context"], 0.95)
        self.assertGreaterEqual(result["trust_score"], 70)

    def test_human_override_persists_context_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_file = Path(tmp) / "active_learning_memory.json"
            record = {
                "respondent_id": "u3",
                "age": 33,
                "education": "History",
                "job_title": "Data Engineer",
                "income": 13000,
                "response_time_seconds": 100,
                "employment_status": "employed",
                "city": "Riyadh",
                "likert_answers": [3, 4, 2, 4],
            }

            engine = DataTrustEngine(memory_path=str(memory_file))
            before = engine.evaluate_record(record)
            added = engine.register_human_override(record, approved=True, reason="تحول مهني معتمد")

            engine_reloaded = DataTrustEngine(memory_path=str(memory_file))
            after = engine_reloaded.evaluate_record(record)

            self.assertTrue(added)
            self.assertGreater(after["layer_scores"]["semantic_context"], before["layer_scores"]["semantic_context"])
            self.assertTrue(memory_file.exists())


if __name__ == "__main__":
    unittest.main()
