"""The "Chat with support" card (web/js/help.js agentChatHtml): a placeholder for the pilot program."""
import re
from pathlib import Path

I18N = (Path(__file__).resolve().parent.parent / "web" / "js" / "i18n.js").read_text(encoding="utf-8")
HELP = (Path(__file__).resolve().parent.parent / "web" / "js" / "help.js").read_text(encoding="utf-8")


def test_card_labels_exist_in_all_seven_languages():
    for key in ["agent_title", "agent_text", "agent_soon", "agent_you", "agent_sees", "agent_sample"]:
        assert len(re.findall(rf'["\s]{key}"?:', I18N)) == 7, key


def test_it_is_only_a_placeholder():
    # The prototype doesn't send anything: the button is disabled and there is no request in the card
    card = HELP[HELP.index("export function agentChatHtml"):]
    assert "disabled" in card and "fetch(" not in card
