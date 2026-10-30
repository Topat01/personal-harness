import os
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")


def run(args, cwd):
    return subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True, capture_output=True)


class EdaTest(unittest.TestCase):
    def test_reports_facts_and_question_hints(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv")
            with open(p, "w") as f:
                f.write("item_id,kind,at,qty,ver\n")
                f.write("A1,PROD,2026-10-01 10:00:00,5,v1.0\nA2,PROD,2026/10/02 10:00,0,1.0\n")
                f.write("A2,PROD,2026/10/02 10:00,0,1.0\nTEST-1,PROD,,3,V1.0\n")
                for i in range(3, 9):
                    f.write(f"A{i},PROD,2026-10-0{i} 10:00:00,{i},v1.0\n")
            out = run([os.path.join(TOOLS, "eda.py"), p], d).stdout
        self.assertIn("행: 10", out)
        self.assertIn("완전히 같은 행(추가분): 1", out)
        self.assertIn("드문 접두어 TEST-", out)
        self.assertIn("0인 값 2개", out)
        self.assertIn("같은 값을 다르게 적은 것으로 보임", out)
        self.assertIn("at: 비어 있는 1건", out)


class CheckSubmitTest(unittest.TestCase):
    def make_repo(self, d, with_test=True, submit=True):
        if with_test:
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertEqual(1, 1)\n")
        git(d, "init", "-q")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "init", "--allow-empty")
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
        if submit:
            with open(os.path.join(d, "SUBMIT.md"), "w") as f:
                f.write(f"## 선택한 판단과 근거\n(커밋 {h})\n## 검증 결과\n## 남은 한계\n")
        with open(os.path.join(d, ".gitignore"), "w") as f:
            f.write("__pycache__/\n.pytest_cache/\n")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "docs")
        git(d, "tag", "submittable-v1")

    def test_exit_2_when_no_tests(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_repo(d, with_test=False)
            r = run([os.path.join(TOOLS, "check_submit.py")], d)
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_exit_0_when_clean(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_repo(d)
            r = run([os.path.join(TOOLS, "check_submit.py"), "SUBMIT.md"], d)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_exit_1_on_missing_file_and_secret(self):
        with tempfile.TemporaryDirectory() as d:
            self.make_repo(d)
            with open(os.path.join(d, "conf.py"), "w") as f:
                f.write('api_key = "abcdefghijklmnop"\n')
            git(d, "add", "-A")
            git(d, "commit", "-qm", "conf")
            r = run([os.path.join(TOOLS, "check_submit.py"), "board.html"], d)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("필수 제출물 없음: board.html", r.stdout)
        self.assertIn("비밀값으로 보임: conf.py", r.stdout)


class PreflightTest(unittest.TestCase):
    def test_runs(self):
        with tempfile.TemporaryDirectory() as d:
            r = run([os.path.join(TOOLS, "preflight.py")], d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("시간 파싱 함정", r.stdout)


class EdaFormatsTest(unittest.TestCase):
    def test_json_and_log(self):
        with tempfile.TemporaryDirectory() as d:
            j, l = os.path.join(d, "a.json"), os.path.join(d, "b.log")
            with open(j, "w") as f:
                f.write('[{"id":1,"q":"x"},{"id":2,"q":null}]')
            with open(l, "w") as f:
                f.write("2026-10-01 10:00:00 INFO a\n2026-10-01T10:00:01Z ERROR b\n")
            out = run([os.path.join(TOOLS, "eda.py"), j, l], d).stdout
        self.assertIn("q: 비어 있는 1건", out)
        self.assertIn("시각 형식이 2가지", out)


class ScanTest(unittest.TestCase):
    def test_finds_readme_lines_tests_and_data(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "tests"))
            os.makedirs(os.path.join(d, "data"))
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("# 과제\n잡담\n## 제출물\n1. report.md\n")
            open(os.path.join(d, "tests", "test_x.py"), "w").close()
            open(os.path.join(d, "data", "a.csv"), "w").close()
            out = run([os.path.join(TOOLS, "scan.py")], d).stdout
        self.assertIn("1. report.md", out)
        self.assertNotIn("잡담", out)
        self.assertIn("tests/test_x.py", out)
        self.assertIn("데이터: data/a.csv", out)


class CheckpointTest(unittest.TestCase):
    def test_start_stage_status(self):
        with tempfile.TemporaryDirectory() as d:
            r1 = run([os.path.join(TOOLS, "checkpoint.py"), "start", "--minutes", "90"], d)
            r2 = run([os.path.join(TOOLS, "checkpoint.py"), "stage", "3"], d)
            r3 = run([os.path.join(TOOLS, "checkpoint.py"), "start"], d)
        self.assertEqual(r1.returncode, 0, r1.stdout)
        self.assertIn("경과 0분", r2.stdout)
        self.assertIn("▶ 3. 합의", r2.stdout)
        self.assertEqual(r3.returncode, 1)


class SetupTest(unittest.TestCase):
    def test_setup_copies_and_rewrites_kit_path(self):
        kit = os.path.dirname(TOOLS)
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(["bash", os.path.join(kit, "setup.sh")], cwd=d, capture_output=True, text=True)
            agents = open(os.path.join(d, "AGENTS.md")).read()
            skills = sorted(os.listdir(os.path.join(d, ".agents", "skills")))
            ignore = open(os.path.join(d, ".gitignore")).read()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("~/kit", agents)
        self.assertIn(kit, agents)
        self.assertIn("design-review", skills)
        self.assertIn(".kit_start", ignore)


if __name__ == "__main__":
    unittest.main()
