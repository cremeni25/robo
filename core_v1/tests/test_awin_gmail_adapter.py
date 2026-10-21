"""Offline checks for Gmail invitation safety and classification."""
import base64
import unittest
from core_v1.app.awin_gmail_adapter import parse_invitation


def message(sender, subject, body, mid="test-id"):
    return {
        "id": mid,
        "payload": {
            "headers": [{"name": "From", "value": sender}, {"name": "Subject", "value": subject}],
            "body": {"data": base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")},
        },
    }


class InvitationAdapterTests(unittest.TestCase):
    def test_realistic_invitation_is_not_publication_authorization(self):
        result = parse_invitation(message(
            "Awin <help@awin.com>",
            "World Businesses for Sale convidou você para fazer parte de seu programa",
            "Leia os termos e condições antes de aceitar o convite.",
        ))
        self.assertEqual(result["external_event_id"], "gmail:test-id")
        self.assertEqual(result["advertiser"], "World Businesses for Sale")
        self.assertNotIn("publication_ready", result)
        self.assertNotIn("email", result)
        self.assertNotIn("body", result)

    def test_rejects_spoofed_sender(self):
        self.assertIsNone(parse_invitation(message(
            "Fake <fake@awin.com.evil.example>",
            "World Businesses for Sale convidou você para fazer parte de seu programa",
            "Convite",
        )))

    def test_rejects_non_invitation(self):
        self.assertIsNone(parse_invitation(message(
            "Awin <no-reply@awin.com>", "Validação de e-mail do novo usuário", "Clique para ativar",
        )))


if __name__ == "__main__":
    unittest.main()
