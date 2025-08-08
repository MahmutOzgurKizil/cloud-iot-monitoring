import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'scoresdb')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin1234')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            player_id VARCHAR(50) PRIMARY KEY,
            score INT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_player_score(player_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT score FROM scores WHERE player_id = %s", (player_id,))
    score = cur.fetchone()
    cur.close()
    conn.close()
    return score['score'] if score else None

def upsert_player_score(player_id, score):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO scores (player_id, score)
        VALUES (%s, %s)
        ON CONFLICT (player_id) DO UPDATE
        SET score = GREATEST(scores.score, EXCLUDED.score)
    """, (player_id, score))
    conn.commit()
    cur.close()
    conn.close()
    
def get_top_scores(limit=100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT player_id, score FROM scores ORDER BY score DESC LIMIT 20")
    top_scores = cur.fetchall()
    cur.close()
    conn.close()
    return top_scores

def delete_all_scores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM scores")
    conn.commit()
    cur.close()
    conn.close()
