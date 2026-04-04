from semantic_router.route import Route
from semantic_router import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2")

finance_route = Route(
    name="finance_route",
    utterances=[
        "What is our revenue this quarter?",
        "Show me the annual report",
        "What is the budget allocation for this year?",
        "How much did we spend on operations?",
        "What are the financial projections?",
        "Show me the Q3 earnings summary",
        "What is the company balance sheet?",
        "What are investor relations documents?",
        "How much profit did we make?",
        "What is the department budget breakdown?",
        "Show vendor payment summary",
        "What are our financial metrics?",
    ],
)

engineering_route = Route(
    name="engineering_route",
    utterances=[
        "What is the system architecture?",
        "Show me the API reference documentation",
        "How do I resolve an incident?",
        "What are the incident runbooks?",
        "How do I onboard to the engineering platform?",
        "What is the technical specification?",
        "What is the database schema?",
        "What happened during the last system outage?",
        "How do I deploy the application?",
        "What is the SLA for the system?",
        "What were the sprint metrics last quarter?",
        "How do I set up the development environment?",
    ],
)

marketing_route = Route(
    name="marketing_route",
    utterances=[
        "How did the marketing campaign perform?",
        "What are the brand guidelines?",
        "What is our market share?",
        "Tell me about our competitors",
        "What were the Q1 marketing results?",
        "What is the customer acquisition cost?",
        "Show me the marketing report",
        "What is our brand logo color palette?",
        "How did the Q4 marketing campaign do?",
        "What is the competitor analysis?",
        "How many customers did we acquire?",
        "What is the marketing budget allocation?",
    ],
)

hr_general_route = Route(
    name="hr_general_route",
    utterances=[
        "What is the company leave policy?",
        "How many days of annual leave do I get?",
        "What are the company benefits?",
        "What is the code of conduct?",
        "Tell me about the employee handbook",
        "What is the maternity leave policy?",
        "What is the company culture?",
        "Who should I contact in HR?",
        "What is the performance review process?",
        "What is the work from home policy?",
        "What are the company policies?",
        "How do I apply for sick leave?",
        "What is the notice period?",
        "Tell me about company values",
    ],
)

cross_department_route = Route(
    name="cross_department_route",
    utterances=[
        "What is the overall company strategy?",
        "Give me a CEO townhall summary",
        "What is FinSolve doing this year?",
        "What are cross-functional goals?",
        "What were the all hands meeting notes?",
        "What are company-wide achievements?",
        "How do the departments interact?",
        "What is the company roadmap?",
        "Tell me about FinSolve Technologies",
        "What are the key company goals?",
        "Give me an overview of the company",
    ],
)

route_layer = SemanticRouter(
    encoder=encoder,
    routes=[finance_route, engineering_route, marketing_route, hr_general_route, cross_department_route],
    auto_sync="local"
)

# Maps each route to the roles that are allowed to access it
ROUTE_ROLE_MAP = {
    "finance_route":          ["finance", "c_level"],
    "engineering_route":      ["engineering", "c_level"],
    "marketing_route":        ["marketing", "c_level"],
    "hr_general_route":       ["employee", "finance", "engineering", "marketing", "c_level"],  # All roles
    "cross_department_route": ["employee", "finance", "engineering", "marketing", "c_level"],  # All roles
    "unclassified":           ["employee", "finance", "engineering", "marketing", "c_level"],  # Default to general
}

# Human-readable access denied messages
ROUTE_DENIED_MESSAGES = {
    "finance_route":     "You don't have access to finance documents. Please contact your Finance department.",
    "engineering_route": "You don't have access to engineering documents. Please contact the Engineering team.",
    "marketing_route":   "You don't have access to marketing documents. Please contact the Marketing team.",
}


def get_route(query: str) -> str:
    """Classify query into a semantic route."""
    try:
        match = route_layer(query)
        return match.name if match and match.name else "unclassified"
    except Exception as e:
        print(f"Routing error: {e}")
        return "unclassified"


def check_rbac_for_route(route_name: str, user_role: str) -> tuple[bool, str]:
    """
    Check if the user's role allows access to this route.
    Returns (has_access, denial_message).
    
    Logs route and role for auditability.
    """
    role_lower = user_role.lower()
    allowed_roles = ROUTE_ROLE_MAP.get(route_name, ["c_level"])
    
    print(f"[AUDIT] Query routed to: {route_name} | User role: {role_lower} | Allowed: {allowed_roles}")
    
    if role_lower in allowed_roles:
        return True, ""
    
    denial_msg = ROUTE_DENIED_MESSAGES.get(
        route_name, 
        f"You don't have access to documents in this category."
    )
    return False, denial_msg
