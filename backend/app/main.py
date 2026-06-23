from fastapi import FastAPI

app = FastAPI(
    title="EventFinder API",
    description="Core API for EventFinder event discovery.",
    version="1.0.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "eventfinder-api",
        "version": "1.0.0",
    }
