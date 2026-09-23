"""Tests for Aniket's command parser, pipeline executor, and combat feedback."""

import os
import sys
import unittest

# Ensure 'src' and project root are on sys.path for direct test execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cybershell.contracts import DEFAULT_BACKLASH_DAMAGE, EngineProtocol  # noqa: E402
from cybershell.engine.interpreter import ShellInterpreter  # noqa: E402


class TestShellInterpreter(unittest.TestCase):
    def test_interpreter_conforms_to_engine_protocol(self):
        self.assertIsInstance(ShellInterpreter(), EngineProtocol)

    def test_tokenizer_preserves_quoted_strings_and_operators(self):
        tokens, error = ShellInterpreter.tokenize('echo "hello cyber world" >> notes.txt')
        self.assertIsNone(error)
        self.assertEqual(tokens, ["echo", "hello cyber world", ">>", "notes.txt"])

    def test_tier_one_commands_and_listing_flags(self):
        shell = ShellInterpreter()
        self.assertEqual(shell.execute("pwd").stdout, "/home/operative\n")
        self.assertEqual(shell.execute("mkdir -p missions/alpha").exit_code, 0)
        self.assertEqual(shell.execute("touch missions/alpha/.token").exit_code, 0)
        listing = shell.execute("ls -la missions/alpha")
        self.assertEqual(listing.exit_code, 0)
        self.assertIn(".token", listing.stdout)
        self.assertIn("-rw-r--r--", listing.stdout)
        self.assertEqual(shell.execute("cd missions/alpha").metadata["cwd"], "/home/operative/missions/alpha")

    def test_file_commands_copy_move_remove_and_chmod(self):
        shell = ShellInterpreter()
        shell.execute("echo payload > source.txt")
        self.assertEqual(shell.execute("cp source.txt copy.txt").exit_code, 0)
        self.assertEqual(shell.execute("mv copy.txt moved.txt").exit_code, 0)
        self.assertEqual(shell.execute("chmod 600 moved.txt").exit_code, 0)
        self.assertEqual(shell.vfs.get_node("moved.txt").mode_octal, "600")
        self.assertEqual(shell.execute("cat moved.txt").stdout, "payload\n")
        self.assertEqual(shell.execute("rm moved.txt").exit_code, 0)
        self.assertFalse(shell.vfs.exists("moved.txt"))

    def test_pipeline_redirection_and_filters(self):
        shell = ShellInterpreter()
        result = shell.execute('echo "Alpha\nBeta\nalpha" | grep -i alpha | wc -l > count.txt')
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(shell.execute("cat count.txt").stdout, "2\n")
        shell.execute("echo gamma >> words.txt")
        shell.execute("echo delta >> words.txt")
        self.assertEqual(shell.execute("tail -n 1 words.txt").stdout, "delta\n")

    def test_unknown_command_and_syntax_error_cause_backlash(self):
        shell = ShellInterpreter()
        unknown = shell.execute("pwdd")
        self.assertEqual(unknown.exit_code, 127)
        self.assertEqual(unknown.backlash_damage, DEFAULT_BACKLASH_DAMAGE)
        self.assertIn("command not found", unknown.stderr)
        malformed = shell.execute("echo payload |")
        self.assertEqual(malformed.exit_code, 2)
        self.assertEqual(malformed.backlash_damage, DEFAULT_BACKLASH_DAMAGE)

    def test_ordinary_filesystem_errors_do_not_cause_backlash(self):
        shell = ShellInterpreter()
        missing = shell.execute("cat missing.txt")
        self.assertEqual(missing.exit_code, 1)
        self.assertEqual(missing.backlash_damage, 0)
        self.assertIn("No such file or directory", missing.stderr)

    def test_sort_less_and_input_redirection(self):
        shell = ShellInterpreter()
        shell.execute('echo "banana\napple\ncherry" > fruits.txt')
        res_sort = shell.execute("sort fruits.txt")
        self.assertEqual(res_sort.stdout, "apple\nbanana\ncherry\n")
        res_rev = shell.execute("sort -r fruits.txt")
        self.assertEqual(res_rev.stdout, "cherry\nbanana\napple\n")
        res_less = shell.execute("less fruits.txt")
        self.assertEqual(res_less.stdout, "banana\napple\ncherry\n")
        res_in = shell.execute("grep apple < fruits.txt")
        self.assertEqual(res_in.stdout, "apple\n")
