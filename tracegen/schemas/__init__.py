from .base import CognitiveLabel, DomainSchema
from .aol import AOLSchema
from .stackoverflow import StackOverflowSchema
from .movielens import MovieLensSchema

SCHEMA_REGISTRY = {
    "aol": AOLSchema,
    "stackoverflow": StackOverflowSchema,
    "movielens": MovieLensSchema,
}
