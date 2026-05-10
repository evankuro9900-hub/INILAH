from app.services.scrapers.multi_league import (
    find_normalized_team_key,
    find_team_stats,
    normalize_team_name,
)


def test_find_normalized_team_key_handles_source_name_variants() -> None:
    candidates = {
        normalize_team_name(team)
        for team in [
            "Bali United FC",
            "Borneo Samarinda",
            "Bhayangkara Presisi Indonesia FC",
            "Madura United",
            "Persebaya Surabaya",
        ]
    }

    assert find_normalized_team_key("Bali United", candidates) == "bali"
    assert find_normalized_team_key("Borneo FC", candidates) == "borneo samarinda"
    assert (
        find_normalized_team_key("Bhayangkara Surabaya", candidates)
        == "bhayangkara presisi indonesia"
    )
    assert find_normalized_team_key("Madura United", candidates) == "madura"


def test_find_normalized_team_key_avoids_ambiguous_token_matches() -> None:
    candidates = {
        normalize_team_name(team)
        for team in ["Manchester United FC", "Manchester City FC", "New York City FC"]
    }

    assert find_normalized_team_key("City", candidates) is None


def test_find_team_stats_uses_fuzzy_normalized_key() -> None:
    team_index = {
        normalize_team_name("Bhayangkara Presisi Indonesia FC"): {
            "name": "Bhayangkara Presisi Indonesia FC",
            "rank": 7,
        }
    }

    assert find_team_stats("Bhayangkara Surabaya", team_index) == {
        "name": "Bhayangkara Presisi Indonesia FC",
        "rank": 7,
    }
