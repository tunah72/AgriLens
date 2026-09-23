"""Agricultural leaf disease data collection and annotation pipeline."""

__all__ = ["main_pipeline"]


def __getattr__(name: str):
    if name == "main_pipeline":
        from crawl.pipeline import main_pipeline

        return main_pipeline
    raise AttributeError(f"module 'crawl' has no attribute '{name}'")
