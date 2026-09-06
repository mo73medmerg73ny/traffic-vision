from fastapi import APIRouter
from app.db.model import get_video, get_tracks_by_video

router = APIRouter(prefix='/videos', tags=['videos'])

@router.get('/tracks/{video_id}')
def get_tracks_by_video_id(video_id: int):
    return get_tracks_by_video(video_id)


@router.get('/{video_id}')
def read_video(video_id: int):
    return get_video(video_id)
