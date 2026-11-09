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
    def make_repo(self, d, with_test=True):
        if with_test:
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertEqual(1, 1)\n")
        git(d, "init", "-q")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "init", "--allow-empty")
        with open(os.path.join(d, "HOW_TO_RUN.md"), "w") as f:
            f.write("실행 방법\n")
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
            r = run([os.path.join(TOOLS, "check_submit.py"), "HOW_TO_RUN.md"], d)
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


class SetupTest(unittest.TestCase):
    def test_setup_copies_and_rewrites_kit_path(self):
        kit = os.path.dirname(TOOLS)
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(["bash", os.path.join(kit, "setup.sh")], cwd=d, capture_output=True, text=True)
            agents = open(os.path.join(d, "AGENTS.md")).read()
            skills = sorted(os.listdir(os.path.join(d, ".agents", "skills")))
            ignore = open(os.path.join(d, ".gitignore")).read()
            notes_exists = os.path.exists(os.path.join(d, "NOTES.md")) and os.path.exists(os.path.join(d, "SPEC.md"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("~/kit", agents)
        self.assertNotIn("<kit>", agents)
        self.assertIn(kit, agents)
        self.assertIn("kickoff", skills)
        self.assertIn("final-docs", skills)
        self.assertTrue(notes_exists)
        self.assertIn("__pycache__/", ignore)


class HomeWorkspaceTest(unittest.TestCase):
    def test_setup_in_home_ignores_dotfiles_and_nested_kit(self):
        kit_src = os.path.dirname(TOOLS)
        with tempfile.TemporaryDirectory() as home:
            for f in [".bashrc", ".profile", "README.md"]:
                open(os.path.join(home, f), "w").close()
            os.makedirs(os.path.join(home, ".config"))
            subprocess.run(["git", "init", "-q"], cwd=home, check=True)
            kit = os.path.join(home, ".kit")
            subprocess.run(["cp", "-R", kit_src, kit], check=True)
            env = dict(os.environ, HOME=home)
            r = subprocess.run(["bash", os.path.join(kit, "setup.sh")], cwd=home, env=env, capture_output=True, text=True)
            ignore = open(os.path.join(home, ".gitignore")).read().split()
            skill = open(os.path.join(home, ".agents", "skills", "kickoff", "SKILL.md")).read()
            status = subprocess.run(["git", "status", "--short", "-uall"], cwd=home, capture_output=True, text=True).stdout
            scan = run([os.path.join(kit, "tools", "scan.py")], home).stdout
        self.assertEqual(r.returncode, 0, r.stderr)
        for p in [".kit/", ".bashrc", ".profile", ".config/"]:
            self.assertIn(p, ignore)
        self.assertIn(kit, skill)
        self.assertNotIn("<kit>", skill)
        self.assertNotIn(".bashrc", status)
        self.assertNotIn(".kit/", status)
        self.assertNotIn(".bashrc", scan)


class ReadmeCheckTest(unittest.TestCase):
    def test_detects_modified_readme_and_missing_named_docs(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("# 과제\n산출물: HOW_TO_RUN.md, AI_COLLABORATION.md, Dockerfile, data/README.md\n")
            with open(os.path.join(d, "HOW_TO_RUN.md"), "w") as f:
                f.write("x\n")
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertTrue(True)\n")
            git(d, "init", "-q")
            git(d, "add", "-A")
            git(d, "commit", "-qm", "start")
            with open(os.path.join(d, "README.md"), "a") as f:
                f.write("내가 고침\n")
            r = run([os.path.join(TOOLS, "check_submit.py")], d)
        self.assertIn("README.md가 처음 커밋된 내용과 달라짐", r.stdout)
        self.assertIn("언급된 파일이 없음: AI_COLLABORATION.md", r.stdout)
        self.assertIn("언급된 파일이 없음: Dockerfile", r.stdout)
        self.assertNotIn("없음: HOW_TO_RUN.md", r.stdout)
        self.assertEqual(r.returncode, 1)


class SkillFrontmatterTest(unittest.TestCase):
    def test_every_skill_has_name_and_plain_description(self):
        import glob
        root = os.path.dirname(TOOLS)
        files = glob.glob(os.path.join(root, ".agents", "skills", "**", "SKILL.md"), recursive=True)
        self.assertGreaterEqual(len(files), 2)
        for f in files:
            fm = open(f, encoding="utf-8").read().split("---")[1]
            lines = {l.split(":", 1)[0]: l.split(":", 1)[1].strip() for l in fm.splitlines() if ":" in l}
            self.assertIn("name", lines, f)
            d = lines.get("description", "")
            self.assertTrue(d, f)
            if d[0] in "\"'":  # 따옴표로 시작하면 같은 따옴표로 끝나야 YAML이 깨지지 않는다
                self.assertTrue(d.endswith(d[0]), f)


class ReadmeBaselineTest(unittest.TestCase):
    """README가 첫 커밋이 아니라 나중에 커밋돼도 오탐하지 않는다."""
    def test_readme_added_after_root_commit_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            git(d, "init", "-q")
            with open(os.path.join(d, ".gitignore"), "w") as f:
                f.write("__pycache__/\n.pytest_cache/\n")
            git(d, "add", "-A")
            git(d, "commit", "-qm", "harness")
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("# 과제\n")
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertTrue(True)\n")
            git(d, "add", "-A")
            git(d, "commit", "-qm", "task")
            git(d, "tag", "submittable-v1")
            r = run([os.path.join(TOOLS, "check_submit.py")], d)
        self.assertNotIn("README.md가 처음", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_uncommitted_readme_is_a_warning(self):
        with tempfile.TemporaryDirectory() as d:
            git(d, "init", "-q")
            git(d, "commit", "-qm", "empty", "--allow-empty")
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("# 과제\n")
            r = run([os.path.join(TOOLS, "check_submit.py")], d)
        self.assertIn("README.md가 아직 커밋되지 않음", r.stdout)


class CheckSubmitJunkTest(unittest.TestCase):
    def test_committed_venv_is_a_problem(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "node_modules", "x"))
            open(os.path.join(d, "node_modules", "x", "i.js"), "w").close()
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertTrue(True)\n")
            git(d, "init", "-q")
            git(d, "add", "-A")
            git(d, "commit", "-qm", "x")
            r = run([os.path.join(TOOLS, "check_submit.py")], d)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("커밋된 잡동사니: node_modules/x/i.js", r.stdout)


class ScanHarnessDirTest(unittest.TestCase):
    """하네스를 숨김 아닌 이름(~/kit 등)으로 받아도 과제 코드로 보지 않는다."""
    def test_visible_kit_dir_is_skipped(self):
        kit_src = os.path.dirname(TOOLS)
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("# 과제\n## 산출물\n- HOW_TO_RUN.md\n")
            subprocess.run(["cp", "-R", kit_src, os.path.join(d, "kit")], check=True)
            out = run([os.path.join(d, "kit", "tools", "scan.py")], d).stdout
        self.assertIn("## README.md", out)
        self.assertNotIn("kit/", out)
        self.assertIn("테스트 파일: 0개", out)
        self.assertNotIn("기존 테스트가 있으면", out)


class SetupEdgeTest(unittest.TestCase):
    def test_rerun_does_not_duplicate_and_keeps_task_agents(self):
        kit = os.path.dirname(TOOLS)
        with tempfile.TemporaryDirectory() as base:
            d = os.path.join(base, "작업 폴더")  # 공백·한글 경로
            os.makedirs(d)
            with open(os.path.join(d, "AGENTS.md"), "w") as f:
                f.write("# 과제가 준 지침\n")
            for _ in range(2):
                r = subprocess.run(["bash", os.path.join(kit, "setup.sh")], cwd=d, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
            agents = open(os.path.join(d, "AGENTS.md")).read()
            ignore = open(os.path.join(d, ".gitignore")).read().splitlines()
        self.assertTrue(agents.startswith("# 과제가 준 지침"))
        self.assertEqual(agents.count("# 작업 지침 (코딩 에이전트용)"), 1)
        self.assertEqual(len(ignore), len(set(ignore)))


class HarnessDocsTest(unittest.TestCase):
    """지침이 다시 커지거나, 지침이 가리키는 스킬·절이 사라지지 않게."""
    root = os.path.dirname(TOOLS)

    def read(self, *p):
        return open(os.path.join(self.root, *p), encoding="utf-8").read()

    def test_size_budget(self):
        self.assertLessEqual(len(self.read("AGENTS.md").splitlines()), 60)
        self.assertLessEqual(len(self.read("templates", "NOTES.md").splitlines()), 60)
        skills = os.listdir(os.path.join(self.root, ".agents", "skills"))
        self.assertLessEqual(len(skills), 5)
        self.assertLessEqual(len(self.read("templates", "SPEC.md").splitlines()), 40)

    def test_skills_are_one_level_deep_and_referenced(self):
        agents = self.read("AGENTS.md")
        for name in os.listdir(os.path.join(self.root, ".agents", "skills")):
            self.assertTrue(os.path.exists(os.path.join(self.root, ".agents", "skills", name, "SKILL.md")), name)
            self.assertIn(f"`{name}`", agents, f"AGENTS.md가 스킬 {name}을 언급하지 않음")

    def test_key_rules_present(self):
        agents, notes = self.read("AGENTS.md"), self.read("templates", "NOTES.md")
        spec = self.read("templates", "SPEC.md")
        engine = self.read(".agents", "skills", "engine", "SKILL.md")
        kickoff = self.read(".agents", "skills", "kickoff", "SKILL.md")
        self.assertIn("지나치게 잘게 쪼개거나", agents)
        self.assertIn("기능당 1~3개", agents)
        self.assertIn("--docker", agents)
        self.assertIn("지금 입력과 맞지 않으면", agents)
        self.assertIn("퇴화하지 않는", agents)
        self.assertIn("확인 퀴즈", agents)
        self.assertIn("담당자 질문 초안", kickoff)
        for k in ["| H1", "| R1", "| Q1", "질문(사람)"]:
            self.assertIn(k, spec)
        self.assertIn("퇴화하지 않는", engine)
        self.assertIn("최대 3개", engine)
        self.assertIn("evaluate", engine)
        self.assertIn("문제 틀 바꾸기", agents)
        self.assertIn("비교 결과", notes)
        self.assertIn("[AI]", notes)
        for n in range(9):
            self.assertIn(f"## {n}.", notes)



class CheckSubmitDockerMissingTest(unittest.TestCase):
    def test_no_docker_command_is_not_run_warning(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "Dockerfile"), "w").write("FROM scratch\n")
            with open(os.path.join(d, "test_a.py"), "w") as f:
                f.write("import unittest\n\nclass T(unittest.TestCase):\n    def test_one(self):\n        self.assertTrue(True)\n")
            with open(os.path.join(d, ".gitignore"), "w") as f:
                f.write("__pycache__/\n.pytest_cache/\n")
            git(d, "init", "-q")
            git(d, "add", "-A")
            git(d, "commit", "-qm", "x")
            env = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + "/usr/bin:/bin")
            env["PATH"] = os.pathsep.join(p for p in env["PATH"].split(os.pathsep) if not os.path.exists(os.path.join(p, "docker")))
            r = subprocess.run([sys.executable, os.path.join(TOOLS, "check_submit.py"), "--docker"], cwd=d, env=env, capture_output=True, text=True)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("docker 명령이 없어", r.stdout)


if __name__ == "__main__":
    unittest.main()
