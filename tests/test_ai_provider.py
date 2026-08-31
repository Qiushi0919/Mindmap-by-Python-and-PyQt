import json
import sys
import unittest
from pathlib import Path
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "源代码" / "源代码"
sys.path.insert(0, str(SOURCE))

from AIProvider import OrcaRouterClient, ProviderError, normalize_markdown


class FakeResponse(object):
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class AIProviderTests(unittest.TestCase):
    def test_normalizes_fenced_markdown(self):
        result = normalize_markdown("```markdown\n# Topic\n## Branch\n### Detail\n```")
        self.assertEqual(result, "# Topic\n## Branch\n### Detail")

    def test_rejects_non_outline_response(self):
        with self.assertRaises(ProviderError):
            normalize_markdown("This is only a paragraph.")

    @mock.patch("AIProvider.request.urlopen")
    def test_calls_openai_compatible_endpoint(self, urlopen):
        urlopen.return_value = FakeResponse({
            "choices": [{"message": {"content": "# Topic\n## Branch"}}]
        })
        client = OrcaRouterClient("sk-orca-test")
        result = client.generate_mindmap("Topic")
        self.assertEqual(result, "# Topic\n## Branch")
        sent_request = urlopen.call_args[0][0]
        self.assertEqual(sent_request.full_url, "https://api.orcarouter.ai/v1/chat/completions")
        self.assertEqual(sent_request.get_header("Authorization"), "Bearer sk-orca-test")


if __name__ == "__main__":
    unittest.main()
