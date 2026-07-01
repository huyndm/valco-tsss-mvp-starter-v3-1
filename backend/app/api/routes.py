from fastapi import APIRouter

router = APIRouter()


@router.get("/tsss/pipeline")
def tsss_pipeline():
    return {
        "pipeline": [
            "raw candidate search up to 1,000",
            "deduplicate",
            "FreeLLMAPI extraction/normalization",
            "hard filter",
            "eligible pool",
            "Top 10 recommended",
            "analyst/user final 3",
            "export/audit",
        ]
    }
