from flask import Flask, request, jsonify, render_template

score_list = []

app = Flask(__name__)

@app.route('/score', methods=['POST'])
def handle_submit_score():

    try:
        player_id = request.form.get('player_id')
        score = int(request.form.get('score'))

        # Validate input
        if not player_id or score is None:
            raise ValueError('Invalid input')

        if not isinstance(score, int):
            raise ValueError('Score must be an integer')

        if score < 0:
            raise ValueError('Score must be a non-negative integer')

        # Check if player already exists
        existing = next((s for s in score_list if s['player_id'] == player_id), None)

        if existing: 
            if score > existing['score']:
                existing['score'] = score
        else:
            score_list.append({'player_id': player_id, 'score': score})
        
        return jsonify({'message': 'Score submitted successfully'}), 200
    
    except ValueError:
        return jsonify({'error': 'Invalid score format' }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/leaderboard', methods=['GET'])
def handle_get_leaderboard():
    if not score_list:
        return jsonify({'message': 'No scores submitted yet'}), 200
    
    sorted_scores = sorted(score_list, key=lambda x: x['score'], reverse=True)
    top_scores = sorted_scores[:100]
    return render_template('leaderboard.html', scores=top_scores), 200