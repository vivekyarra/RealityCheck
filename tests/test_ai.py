from app.ai import GeminiExpectationAgent, create_adk_fleet
from app.config import Settings
from app.demo import WELCOME_EMAIL


def test_deterministic_extraction_is_evidence_bound():
    agent = GeminiExpectationAgent(Settings(google_api_key=None))
    contract, mode = agent.extract("welcome.txt", WELCOME_EMAIL, "FiberMax")
    assert mode == "deterministic-local"
    assert contract.counterparty == "FiberMax"
    assert {term.key for term in contract.terms} == {
        "monthly_price",
        "installation_fee",
        "duration_months",
    }
    assert all(term.evidence_id for term in contract.terms)
    assert len(contract.evidence) == 3


def test_ambiguous_evidence_stays_low_confidence():
    agent = GeminiExpectationAgent(Settings(google_api_key=None))
    contract, _ = agent.extract("vague.txt", "Service should usually be available soon.")
    assert contract.confidence == 0.35
    assert contract.terms[0].kind == "soft"


def test_google_adk_fleet_constructs_with_current_sdk():
    fleet = create_adk_fleet(Settings())
    assert fleet.name == "realitycheck_fleet"
    assert [agent.name for agent in fleet.sub_agents] == [
        "expectation_agent",
        "observation_agent",
        "judge_agent",
        "resolution_agent",
        "owed_agent",
        "guardian_agent",
    ]
