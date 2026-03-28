"""StackOverflow Q&A domain-adapted IFT schema."""

from typing import List
from .base import DomainSchema


SO_LABEL_SCHEMA = """
# Cognitive Label Schema for Stack Overflow (Information Foraging Theory)

You are annotating a Stack Overflow user's activity session. Unlike web search, SO is a knowledge-sharing platform where users both seek AND provide information. Apply IFT to this collaborative foraging context.

## Label Definitions with Domain-Specific Mappings:

1. **FollowingScent**: User initiates a knowledge-seeking or knowledge-sharing action with clear intent.
   - POST_QUESTION: User identifies an information need and formulates it as a question (primary foraging initiation)
   - VOTE_BOUNTY_START: User offers a bounty to attract better answers (intensifying the search)
   - VOTE_FAVORITE: User bookmarks a post for future reference (identifying a promising scent trail)
   - Key signal: The user is actively seeking or organizing information with clear purpose

2. **ApproachingSource**: User engages with a specific post to investigate or evaluate its information.
   - COMMENT on a question: User asks for clarification or seeks more details (approaching the source)
   - VOTE_UP on a question: User validates that a question is worth investigating
   - Key signal: The user is drilling into a specific piece of content to extract or evaluate information

3. **DietEnrichment**: User contributes knowledge or refines existing content, enriching the information environment.
   - EDIT_BODY / EDIT_TITLE / EDIT_TAGS: User improves a post's quality or accuracy
   - EDIT_INITIAL_BODY / EDIT_INITIAL_TITLE / EDIT_POST_TAGS: User crafts the initial version of their contribution
   - COMMENT that provides additional information, clarification, or context
   - Key signal: The user is ADDING or IMPROVING information in the ecosystem

4. **PoorScent**: User encounters low-quality or unhelpful content.
   - VOTE_DOWN: User explicitly signals that content is unhelpful or incorrect
   - COMMENT that expresses disagreement, points out errors, or criticizes approach
   - Key signal: Negative evaluation of information quality
   - IMPORTANT: Do NOT default to PoorScent. Only use when there is a clear negative signal.

5. **LeavingPatch**: User disengages from a topic thread after extended interaction without resolution.
   - VOTE_BOUNTY_CLOSE: Bounty expires without satisfactory answer
   - Final event in a session after multiple interactions on the same post without resolution
   - Key signal: Sustained engagement that ends without a clear positive outcome

6. **ForagingSuccess**: User finds or creates a satisfactory answer.
   - POST_ANSWER: User formulates and shares a solution (successful knowledge contribution)
   - VOTE_ACCEPT_ANSWER: User accepts an answer as the solution to their question
   - VOTE_UP on an answer: User validates that an answer is helpful and correct
   - Key signal: Positive resolution of an information need -- someone got their answer

## Balance Guidance:
- POST_QUESTION should typically be FollowingScent (clear intent to find information)
- POST_ANSWER should typically be ForagingSuccess (the user found/created a solution)
- EDITs (all types) should typically be DietEnrichment (improving information quality)
- COMMENTs depend on context: clarifying = ApproachingSource, adding info = DietEnrichment, criticizing = PoorScent
- VOTE_UP on answers = ForagingSuccess; VOTE_UP on questions = ApproachingSource
- VOTE_DOWN = PoorScent (clear negative signal)
- Do not over-assign any single label. Consider the sequential context of the session.
"""


class StackOverflowSchema(DomainSchema):
    domain = "stackoverflow"
    action_types: List[str] = [
        "POST_QUESTION", "POST_ANSWER",
        "COMMENT",
        "VOTE_UP", "VOTE_DOWN", "VOTE_ACCEPT_ANSWER", "VOTE_FAVORITE",
        "VOTE_BOUNTY_START", "VOTE_BOUNTY_CLOSE", "VOTE_OTHER",
        "EDIT_INITIAL_TITLE", "EDIT_INITIAL_BODY", "EDIT_POST_TAGS",
        "EDIT_TITLE", "EDIT_BODY", "EDIT_TAGS", "EDIT_OTHER",
    ]

    def get_label_schema_text(self) -> str:
        return SO_LABEL_SCHEMA
