from .aol_loader import AOLLoader
from .stackoverflow_loader import StackOverflowLoader
from .movielens_loader import MovieLensLoader

LOADER_REGISTRY = {
    "aol": AOLLoader,
    "stackoverflow": StackOverflowLoader,
    "movielens": MovieLensLoader,
}
