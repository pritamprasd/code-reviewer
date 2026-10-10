"""
Unit & Integration Tests for Code Reviewer Agent
"""

import os
import unittest
from core.diff_parser import DiffParser
from core.git_reader import GitReader
from core.skill_manager import SkillManager
from core.reviewer_agent import ReviewerAgent, ReviewComment


class TestDiffParser(unittest.TestCase):
    def test_spring_boot_diff_parsing(self):
        sample_path = os.path.join(
            os.path.dirname(__file__), "..", "test_samples", "sample_spring_boot.diff"
        )
        with open(sample_path, "r", encoding="utf-8") as f:
            diff_text = f.read()

        files = DiffParser.parse(diff_text)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].class_or_symbol_name, "OrderController")
        self.assertEqual(files[1].class_or_symbol_name, "OrderService")

        # Check line numbers mapped
        line_nos = files[0].get_added_or_modified_line_numbers()
        self.assertIn(14, line_nos)
        self.assertIn(18, line_nos)

    def test_react_diff_parsing(self):
        sample_path = os.path.join(
            os.path.dirname(__file__), "..", "test_samples", "sample_react.diff"
        )
        with open(sample_path, "r", encoding="utf-8") as f:
            diff_text = f.read()

        files = DiffParser.parse(diff_text)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].class_or_symbol_name, "UserProfile")


class TestSkillManager(unittest.TestCase):
    def test_skills_loading_and_autodetect(self):
        mgr = SkillManager()
        names = mgr.get_skill_names()
        self.assertIn("spring-boot-reviewer", names)
        self.assertIn("react-js-reviewer", names)
        self.assertIn("clean-code-reviewer", names)
        self.assertIn("security-reviewer", names)

        # Test Java autodetect
        detected_java = mgr.auto_detect_skills(
            ["src/main/java/com/example/OrderService.java"],
            "@Service public class OrderService",
        )
        self.assertIn("spring-boot-reviewer", detected_java)

        # Test React autodetect
        detected_react = mgr.auto_detect_skills(
            ["src/components/UserProfile.tsx"],
            "useEffect(() => {}, [])",
        )
        self.assertIn("react-js-reviewer", detected_react)


class TestReviewerFormatting(unittest.TestCase):
    def test_comment_regex_parsing(self):
        sample_llm_output = """
UserService->45->Missing @Transactional annotation on method that modifies database state.
OrderController->82->[Critical] Input DTO is missing @Valid annotation, allowing unvalidated payloads.
UserProfile->24->[Suggestion] useEffect missing 'fetchUserData' in its dependency array.
"""
        agent = ReviewerAgent(None, None, None, None)
        comments = agent._parse_and_validate_comments(sample_llm_output, [])

        self.assertEqual(len(comments), 3)
        self.assertEqual(comments[0].target_class, "UserService")
        self.assertEqual(comments[0].line_number, 45)
        self.assertEqual(
            comments[0].to_standard_format(),
            "UserService->45->Missing @Transactional annotation on method that modifies database state.",
        )

        self.assertEqual(comments[1].severity, "Critical")
        self.assertEqual(comments[2].severity, "Suggestion")


class TestInstructionManager(unittest.TestCase):
    def test_parent_and_skill_instructions(self):
        from core.instruction_manager import InstructionManager

        im = InstructionManager()
        parent_text = im.get_parent_instructions()
        self.assertIn("class->line_number->Review comment", parent_text)

        # Check spring boot custom instruction
        spring_inst = im.get_skill_custom_instructions("spring-boot-reviewer")
        self.assertIn("Spring Boot", spring_inst)

        # Test layered prompt generation
        layered = im.build_layered_prompt(["spring-boot-reviewer", "react-js-reviewer"])
        self.assertIn("GLOBAL INHERITED INSTRUCTIONS", layered)
        self.assertIn("SPRING-BOOT-REVIEWER", layered)


if __name__ == "__main__":
    unittest.main()
