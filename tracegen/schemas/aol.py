"""AOL Web Search domain-adapted IFT schema."""

from typing import List
from .base import DomainSchema


AOL_LABEL_SCHEMA = """
# Cognitive Label Schema for Web Search (Information Foraging Theory)

You are annotating a web search session from the AOL query log. The user performs QUERY, SERP_VIEW, and CLICK actions.

## Label Definitions with Domain-Specific Mappings:

1. **FollowingScent**: User issues a QUERY with clear, specific intent that demonstrates they have identified a promising information trail.
   - Typical action: QUERY with specific, well-formed terms (e.g., "best espresso machine under $500")
   - Key signal: The query shows the user knows WHAT they are looking for
   - NOT applicable when: Query is a vague reformulation after failed attempts

2. **ApproachingSource**: User CLICKs on a search result, indicating they found a result with strong enough information scent to investigate.
   - Typical action: CLICK on a SERP result
   - Key signal: User actively navigates to a document from the search results
   - Also applies to: SERP_VIEW when results clearly match the query intent (titles align with query)

3. **DietEnrichment**: User modifies/refines their query to broaden or narrow their search scope.
   - Typical action: QUERY that is a reformulation of a previous query (adding terms, removing terms, rephrasing)
   - Key signal: The NEW query is related to a PREVIOUS query but strategically adjusted
   - Examples: "laptops" -> "lightweight laptops for travel", "python error" -> "python TypeError list index"
   - NOT applicable when: Query is completely unrelated to previous queries

4. **PoorScent**: Current search results page offers no promising leads. The user views SERP results but finds nothing worth clicking.
   - Typical action: SERP_VIEW followed by a new QUERY (no CLICK between them)
   - Key signal: User saw results but chose not to click any -- the patch was barren
   - Also applies to: CLICK on a result that was immediately followed by return-to-SERP and new query
   - IMPORTANT: Do NOT default to PoorScent when uncertain. Consider FollowingScent or DietEnrichment first.

5. **LeavingPatch**: User abandons a topic entirely after multiple unsuccessful attempts.
   - Typical action: Final event in a session, OR a dramatic topic shift after failed searches
   - Key signal: Multiple failed queries on the same topic followed by session end or complete topic change
   - Requires context: Must see prior failed attempts (PoorScent events) before this label applies

6. **ForagingSuccess**: User found what they needed from the search results.
   - Typical action: CLICK on a result that is the final action in a session (user found their answer)
   - Also applies to: SERP_VIEW where the answer appears directly in snippet/title (no click needed)
   - Key signal: Session ends after a satisfying interaction, or user moves to a completely new unrelated topic

## Balance Guidance:
- In web search, most queries DO have clear intent (FollowingScent) or are refinements (DietEnrichment)
- CLICKs almost always indicate ApproachingSource -- the user chose to investigate
- Only use PoorScent when there is clear evidence of failed SERP viewing (no clicks after viewing results)
- ForagingSuccess should be considered for any session-ending click that matches the query intent
- Do NOT over-assign PoorScent. A query without clicks is not automatically PoorScent if the user refined it (that's DietEnrichment) or if the session just started (that's FollowingScent).
"""


class AOLSchema(DomainSchema):
    domain = "aol"
    action_types: List[str] = ["QUERY", "SERP_VIEW", "CLICK"]

    def get_label_schema_text(self) -> str:
        return AOL_LABEL_SCHEMA
