import db
from redis_client import rc
import kafka_client as kc
from flask import Flask, request, jsonify, render_template
import json

app = Flask(__name__)

@app.route('/score', methods=['POST'])
def handle_submit_score():
    try:
        player_id = request.form.get('player_id')
        score_raw = request.form.get('score')

        # Validate input
        if player_id is None or score_raw is None:
            raise ValueError('Missing player_id or score')
        try:
            score = int(score_raw)
        except ValueError:
            raise ValueError('Score must be an integer')
        if score < 0:
            raise ValueError('Score must be non-negative')
        
        # Upsert score with Kafka
        kc.send_score_update(player_id, score)
        return jsonify({'message': 'Score submitted successfully'}), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def handle_get_leaderboard():
    try:
        cache = rc.get("leaderboard")
        if cache:
            top_scores = json.loads(cache) # Cache hit
        else:
            top_scores = db.get_top_scores() # Cache miss
            rc.set("leaderboard", json.dumps(top_scores), ex=30)
        return render_template('leaderboard.html', scores=top_scores), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/delete-all', methods=['POST'])
def handle_delete_all():
    try:
        db.delete_all_scores()
        rc.delete("leaderboard")
        return jsonify({'message': 'All scores deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    db.init_db()  
    app.run(host='0.0.0.0', port=5000)
