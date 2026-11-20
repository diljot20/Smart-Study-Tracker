import unittest
from app import calculate_points, generate_feedback


class TestStudyTracker(unittest.TestCase):

    def test_high_focus_points(self):
        result = calculate_points(25, 2, "High")
        self.assertEqual(result, 27)

    def test_medium_focus_points(self):
        result = calculate_points(25, 1, "Medium")
        self.assertEqual(result, 26)

    def test_points_never_negative(self):
        result = calculate_points(0, 5, "Low")
        self.assertEqual(result, 0)

    def test_high_focus_feedback(self):
        result = generate_feedback(25, 1, "High")
        self.assertEqual(result, "Great focus! Keep it up.")

    def test_too_many_breaks_feedback(self):
        result = generate_feedback(25, 3, "High")
        self.assertEqual(result, "You are taking too many breaks.")


if __name__ == "__main__":
    unittest.main()