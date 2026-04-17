"""
Business logic services
"""

def __getattr__(name):
    if name == 'AnnotationService':
        from app.services.annotation_service import AnnotationService
        return AnnotationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['AnnotationService']

