from clienthunter.models import Business
from clienthunter.scoring import level_for, score_all, score_business


def test_no_website_max_opportunity():
    biz = score_business(Business(name="Ghost"))
    # 50 no website + 20 no phone + 15 no hours + 10 no email + 5 no address
    assert biz.opportunity_score == 100
    assert biz.opportunity_level == "high"
    assert any("no website" in r for r in biz.reasons)


def test_fully_present_scores_zero():
    biz = score_business(Business(
        name="Modern", website="https://x.example.com", phone="123",
        email="a@b.c", opening_hours="Mo 9-5", address="1 Street"))
    assert biz.opportunity_score == 0
    assert biz.opportunity_level == "low"


def test_http_only_website_partial():
    biz = score_business(Business(
        name="Http", website="http://x.example.com", phone="123",
        email="a@b.c", opening_hours="Mo 9-5", address="1 Street"))
    assert biz.opportunity_score == 25
    assert biz.opportunity_level == "low"


def test_missing_phone_and_hours_only_with_https():
    biz = score_business(Business(
        name="Partial", website="https://x.example.com",
        email="a@b.c", address="1 Street"))
    assert biz.opportunity_score == 20 + 15
    assert biz.opportunity_level == "low"


def test_levels():
    assert level_for(100) == "high"
    assert level_for(70) == "high"
    assert level_for(69) == "medium"
    assert level_for(40) == "medium"
    assert level_for(39) == "low"
    assert level_for(0) == "low"


def test_score_all_sorted_best_lead_first():
    low = Business(name="Aaa Modern", website="https://x.example.com", phone="1",
                   email="a@b.c", opening_hours="Mo", address="1 St")
    high = Business(name="Zzz Ghost")
    scored = score_all([low, high])
    assert scored[0].name == "Zzz Ghost"
    assert scored[0].opportunity_score > scored[1].opportunity_score
