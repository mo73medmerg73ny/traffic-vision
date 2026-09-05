import os
import psycopg2

def get_conn():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(database_url)

def db_init():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
       CREATE TABLE IF NOT EXISTS videos(
                id SERIAL PRIMARY KEY,
                filename TEXT,
                status TEXT,
                total_vehicles INTEGER
                )
    """)

    cur.execute("""
           CREATE TABLE IF NOT EXISTS tracks(
                    id SERIAL PRIMARY KEY,
                    video_id INTEGER REFERENCES videos(id),
                    vehicle_class TEXT,
                    first_seen_seconds FLOAT
                    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    

def insert_video_info(filename, status, total_vehicles):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO videos (filename, status, total_vehicles)  VALUES (%s, %s, %s)  RETURNING id;",
        (filename, status, total_vehicles)
    )

    video_id = cur.fetchall()[0]

    conn.commit()
    cur.close()
    conn.close()

    return video_id

def update_video_status(video_id, status, total_vehicles=None):
    conn = get_conn()
    cur = conn.cursor()

    if total_vehicles is not None:
        cur.execute(
            "UPDATE videos SET status = %s, total_vehicles = %s WHERE id = %s;",
            (status, total_vehicles, video_id)
        )
    else:
        cur.execute(
            "UPDATE videos SET status = %s WHERE id = %s;",
            (status, video_id)
        )

    conn.commit()
    cur.close()
    conn.close()


def insert_tracks_info(video_id, vehicle_class, first_seen_seconds):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO tracks (video_id, vehicle_class, first_seen_seconds) VALUES (%s, %s, %s);",
        (video_id, vehicle_class, first_seen_seconds)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_video(video_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, filename, status, total_vehicles, FROM videos WHERE id = %s",
        (video_id,)
    )

    row = cur.fetchall()

    cur.close()
    conn.close() 

    if row is None:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "status": row[2],
        "total_vehicles": row[3]
    }

def get_tracks_by_video(video_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, vehicle_class,  first_seen_seconds FROM tracks WHERE video_id = %s",
        (video_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id" : row[0],
            "vehicle_class" : row[1],
            "first_seen_seconds" : row[2]
        }
        for row in rows
    ]
