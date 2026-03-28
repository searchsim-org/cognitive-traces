"""MovieLens RecSys domain-adapted IFT schema."""

from typing import List
from .base import DomainSchema


ML_LABEL_SCHEMA = """
# Cognitive Label Schema for MovieLens (Information Foraging Theory)

You are annotating a MovieLens user's movie rating session. In this domain, "foraging" means exploring movies, evaluating them, and building/refining taste preferences. The content field contains JSON with movie_id, movie_title, rating, and optionally system_rating, elicit_rating, predict_rating, and certainty.

## Label Definitions with Domain-Specific Mappings:

1. **FollowingScent**: User continues exploring within a genre, series, director, or thematic thread they have been following.
   - RATE: Rating a movie that shares genre/director/actor/era with recently-rated movies (sequential thematic exploration)
   - BELIEF_PREDICT: User predicts their rating for a movie in a familiar genre (following a known information trail)
   - Key signal: The movie being rated is thematically connected to the user's recent ratings
   - Example: After rating "The Matrix" and "Blade Runner", rating "Inception" (all sci-fi)

2. **ApproachingSource**: User investigates a specific movie recommendation or a movie that caught their attention.
   - RATE: When the user rates a movie close to the system's predicted rating (they agreed with the recommendation scent; within +/- 0.5 of system_rating)
   - BELIEF_ELICIT: User's elicited belief about a movie -- they are evaluating whether to approach this content
   - Key signal: Rating aligns with system_rating, indicating the recommendation led them correctly

3. **DietEnrichment**: User explores a new genre, era, or style they haven't rated before, broadening their taste.
   - RATE: Rating a movie in a genre/era distinctly different from recent ratings (branching out)
   - Key signal: Clear thematic shift from the user's recent pattern
   - Example: After several action movies, rating a documentary or a romance

4. **PoorScent**: User rates a movie significantly lower than expected, indicating a mismatch between expectation and reality.
   - RATE with rating <= 2.0: User found the movie genuinely poor
   - RATE where rating is much lower than system_rating (difference >= 1.5): Recommendation led user astray
   - Key signal: Strong negative rating or large gap between expected and actual enjoyment
   - IMPORTANT: A rating of 3.0 is NEUTRAL, not PoorScent. Only clearly negative experiences (1.0-2.0) qualify.

5. **LeavingPatch**: User stops exploring a genre/theme after a series of disappointments.
   - Final RATE in a sequence of low-rated movies in the same genre
   - Key signal: Multiple consecutive PoorScent events in the same genre followed by a genre switch or session end
   - Requires context: Must see prior negative ratings before this label applies

6. **ForagingSuccess**: User rates a movie highly, indicating they found something they truly enjoyed.
   - RATE with rating >= 4.0: User found a movie they liked
   - RATE where rating matches or exceeds system_rating AND rating >= 4.0: Recommendation was a hit
   - BELIEF_PREDICT with high certainty AND the actual rating later confirms the prediction
   - Key signal: High satisfaction with the movie experience

## Balance Guidance:
- High ratings (4.0-5.0) should generally be ForagingSuccess
- Low ratings (1.0-2.0) should generally be PoorScent
- Medium ratings (2.5-3.5) require sequential context:
  - Same genre as recent ratings → FollowingScent
  - New genre exploration → DietEnrichment
  - Close to system_rating → ApproachingSource
- Sequential genre analysis matters: look at the genre progression across the session
- The gap between system_rating and actual rating is a strong signal
- Do NOT over-assign PoorScent. Medium ratings are not poor; only 1.0-2.0 qualifies.
"""


class MovieLensSchema(DomainSchema):
    domain = "movielens"
    action_types: List[str] = ["RATE", "BELIEF_ELICIT", "BELIEF_PREDICT"]

    def get_label_schema_text(self) -> str:
        return ML_LABEL_SCHEMA
