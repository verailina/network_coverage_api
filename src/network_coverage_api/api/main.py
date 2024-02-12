import uvicorn
from fastapi import FastAPI
from network_coverage_api.api.network_coverage_router import NetworkCoverageRouter


app = FastAPI()

app.include_router(
    NetworkCoverageRouter,
    prefix="/network_coverage",
    tags=["Network Coverage"],
)

if __name__ == "__main__":
    uvicorn.run(
        "network_coverage_api.api.main:app", host="127.0.0.1", port=8088, log_level="info"
    )
