"""Number check (issue #20): every number the AI writes must be in the data it was given."""
import pytest

from app import catalog, checks, config, explain, pipeline

FIELDS = {"doc_type": "traffic_fine", "emirate": "Dubai", "issuing_authority": "Dubai Police",
          "reference_number": "48812", "amount_aed": 600, "issue_date": "2026-10-20",
          "deadline_date": "2026-11-03", "subject": "Exceeding the speed limit by 30 km/h",
          "key_points": ["4 black points"], "keywords": ["speed"], "readable": True, "confidence": 0.9}
DUBAI = explain._public(next(s for s in catalog.load() if s["id"] == "dubai-traffic-fine"))


def ex(**parts):
    base = {"what_it_is": "A speeding fine from Dubai Police.", "cost": "AED 600.", "deadline": "Pay soon.",
            "next_steps": ["Open the official link."]}
    base.update(parts)
    return base


def test_reads_numbers_in_every_script():
    assert checks.numbers("AED 1,000 and 177.75") == {1000.0, 177.75}
    assert checks.numbers("٦٠٠ درهم و ١٬٠٠٠") == {600.0, 1000.0}       # Arabic digits
    assert checks.numbers("६०० ৬০০ ൬൦൦ ۶۰۰") == {600.0}                  # Hindi, Bengali, Malayalam, Urdu


def test_numbers_from_the_data_pass_in_any_format():
    good = ex(cost="You need to pay AED 600.00, plus the AED 20 fee: AED 620 in total.",
              deadline="Pay by 3 November 2026 (03/11/2026), 5 days left.",
              what_it_is="You drove 30 km/h over the limit and got 4 black points.")
    assert checks.unsupported(good, FIELDS, DUBAI, 5) == []


def test_invented_discount_and_deadline_are_caught():
    bad = ex(cost="Pay within 60 days to get a 35% discount.", deadline="You have 24 hours.")
    assert checks.unsupported(bad, FIELDS, DUBAI, 5) == ["60", "35", "24"]


def test_numbers_in_other_scripts_are_checked_too():
    assert checks.unsupported(ex(cost="المبلغ ٦٠٠ درهم"), FIELDS, DUBAI, 5) == []
    assert checks.unsupported(ex(cost="خصم ٣٥٪"), FIELDS, DUBAI, 5) == ["٣٥"]


def test_reference_number_is_never_allowed():
    assert checks.unsupported(ex(what_it_is="Fine number 48812."), FIELDS, DUBAI, 5) == ["48812"]


def test_suggested_questions_are_not_checked():
    assert checks.unsupported(ex(suggested_questions=["Can I pay in 3 or 4 instalments?"]), FIELDS, DUBAI, 5) == []


@pytest.fixture
def ai_explanations(monkeypatch):
    """Make explain.explain return the given answers in order, and record the warnings it got."""
    monkeypatch.setattr(config, "MOCK_AI", False)
    calls = []

    def install(*answers):
        it = iter(answers)
        monkeypatch.setattr(explain, "explain", lambda f, s, d, lang, warning=None, simple=False: (calls.append(warning), next(it))[1])
        return calls
    return install


def test_good_answer_passes_first_time(ai_explanations):
    calls = ai_explanations(ex())
    text, outcome = pipeline.explain_checked(FIELDS, catalog.load()[0], 5, "en")
    assert outcome == "passed" and calls == [None]


def test_invented_number_gets_one_retry_with_a_warning(ai_explanations):
    calls = ai_explanations(ex(cost="35% off if you pay today."), ex())
    text, outcome = pipeline.explain_checked(FIELDS, catalog.load()[0], 5, "en")
    assert outcome == "retried" and text == ex()
    assert calls[0] is None and "35" in calls[1] and "NOT in DATA" in calls[1]


def test_still_wrong_after_retry_uses_the_data_only_template(ai_explanations):
    ai_explanations(ex(cost="35% off."), ex(cost="Now 25% off."))
    text, outcome = pipeline.explain_checked(FIELDS, catalog.load()[0], 5, "en")
    assert outcome == "template"
    assert text["cost"] == "The amount on the document is AED 600."
    assert "03/11/2026" in text["deadline"] and "5 days left" in text["deadline"]


@pytest.mark.parametrize("lang", list(config.LANGUAGES))
def test_template_passes_its_own_check_in_every_language(lang):
    for days in (5, 1, 0, -3, None):
        t = checks.template(FIELDS, days, lang)
        assert all(t[k] for k in ("what_it_is", "cost", "deadline", "next_steps"))
        assert checks.unsupported(t, FIELDS, None, days) == [], (lang, days)
    no_data = checks.template({"doc_type": "tenancy_contract"}, None, lang)
    assert checks.unsupported(no_data, {}, None, None) == []


def test_counts_are_kept_for_the_health_page():
    before = checks.COUNTS["passed"]
    checks.record("passed")
    assert checks.COUNTS["passed"] == before + 1
