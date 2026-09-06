from fastapi import APIRouter
from app.db.model import get_video, get_tracks_by_video

router = APIRouter(prefix='/videos', tags=['videos'])

def get_conn():
    return psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

@router.get('/tracks/{video_id}')
def get_tracks_by_video_id(video_id: int):
    return get_tracks_by_video(video_id)


@router.get('/{video_id}')
def read_video(video_id: int):
    return get_video(video_id)

@router.delete("/reset-db")
def reset_database():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tracks;")
    cur.execute("DELETE FROM videos;")
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "تم تصفير قاعدة البيانات"}
