from fastapi import APIRouter


router = APIRouter()


@router.get("/passes")
def view_pass(s_id: int, gs_id: int):
    pass
    # Check API for new passes

    # Check cache for passes

    # Check api




def cache_passes():
    """Get satellite-groundstation passes from API."""
