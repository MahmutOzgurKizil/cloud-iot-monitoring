import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0
)

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
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

@app.route('/score', methods=['POST'])
def handle_submit_score():
    try:
        player_id = request.form.get('player_id')
        score_raw = request.form.get('score')

        if player_id is None or score_raw is None:
            raise ValueError('Missing player_id or score')

        try:
            score = int(score_raw)
        except ValueError:
            raise ValueError('Score must be an integer')

        if score < 0:
            raise ValueError('Score must be non-negative')

        conn = get_db_connection()
        cur = conn.cursor()
        
        redis_client.get(player_id)
        cur.execute("SELECT score FROM scores WHERE player_id = %s", (player_id,))
        existing = cur.fetchone()

        if existing:
            if score > existing[0]:
                cur.execute("UPDATE scores SET score = %s WHERE player_id = %s", (score, player_id))
        else:
            cur.execute("INSERT INTO scores (player_id, score) VALUES (%s, %s)", (player_id, score))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'Score submitted successfully'}), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def handle_get_leaderboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT player_id, score FROM scores ORDER BY score DESC LIMIT 100")
        top_scores = cur.fetchall()
        cur.close()
        conn.close()

        return render_template('leaderboard.html', scores=top_scores), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/delete-all', methods=['POST'])
def handle_delete_all():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM scores")
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': 'All scores deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
