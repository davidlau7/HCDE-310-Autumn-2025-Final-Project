import json

from flask import Flask, redirect, session, url_for, render_template, request, jsonify
from authlib.integrations.flask_client import OAuth, OAuthError
from projectsecrets import client_id, client_secret, secret_key

app = Flask(__name__)
app.secret_key = secret_key

oauth = OAuth(app)
oauth.register(
    name="spotify",
    client_id=client_id,
    client_secret=client_secret,
    authorize_url="https://accounts.spotify.com/authorize",
    access_token_url="https://accounts.spotify.com/api/token",
    api_base_url="https://api.spotify.com/v1/",
    client_kwargs={
        "scope": "playlist-read-private playlist-read-collaboration playlist-modify-private playlist-modify-public"
    }
)

@app.route("/")
def index():
    try:
        token = session["spotify-token"]["access_token"]
    except KeyError:
        return redirect(url_for("login"))
    data = oauth.spotify.get("me/playlists", token=token).text
    return render_template("index.html", data=json.loads(data))

@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    print(redirect_uri)
    return oauth.spotify.authorize_redirect(redirect_uri)

@app.route("/spotify-authorize")
def authorize():
    try:
        token = oauth.spotify.authorize_access_token()
        session["spotify-token"] = token
    except OAuthError:
        return redirect(url_for("login"))
    return redirect(url_for("index"))

@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "POST":
        return None