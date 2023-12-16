from flask import Flask, render_template, request, session, url_for, redirect, flash
import main
from tm_keys import TM_KEY

app = Flask(__name__)
app.secret_key = 'your_flask_secret_key'
app.config['SESSION_COOKIE_SECURE'] = True

@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get("access_token"):
        return redirect(url_for("login"))
    token = main.get_token()
    if token != session["access_token"]:
        session["access_token"] = token

    if request.method == "POST":
        try:
            artist_name = request.form["artist"]
            session["artist_name"] = artist_name
        except:
            artist_name = session["artist_name"]
        action = request.form.get("action")
        try:
            related_artist = main.search_and_recommend_artists(token, artist_name)
            # session["related_artist"] = related_artist
        except Exception as e:
            print(f"Error making API request: {e}")
            flash("Error getting related artists. Please try again.", "error")
            return redirect(url_for('index'))
        if related_artist is not None:
            g = main.build_graph(related_artist)
            top5 = main.find_top_5_similar_artists(g)
            session["top5"] = top5
            if session["top5"]:
                if action == "get_events":
                    # Perform action for the "Get events" button
                    artist_name = session["artist_name"]
                    top5 = session.get("top5")
                    events = main.get_event_list(top5, TM_KEY)
                    print("get event button clicked!")
                    return render_template('index.html', artist = artist_name, top5=top5, events=events)
            return render_template('index.html', artist = artist_name, top5=top5)
        else:
            # Handle the case where the API request fails
            flash("Error getting related artists. Please try again.", "error")

    
    return render_template('index.html')


@app.route('/callback')
def callback():
    main.load_dotenv()
    client_id = main.client_id
    client_secret = main.client_secret
    token = main.get_token()
    session['access_token'] = token
    session['refresh_token'] = token
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)