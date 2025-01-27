import logging

from flask import Flask, render_template, request
from flask_caching import Cache
from flask_socketio import SocketIO, emit, join_room, rooms

from config import settings as arena_settings
from matches.match_results import match_results
from screens.user_screens import user_screens
from truefinals_api.wrapper import TrueFinals

logging.basicConfig(level="INFO")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.register_blueprint(user_screens, url_prefix="/screens")
app.register_blueprint(match_results, url_prefix="/matches")

app.config["SECRET_KEY"] = "secret secret key (required)!"
socketio = SocketIO(app)

cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
cache.init_app(app)

truefinals = TrueFinals()


@app.route("/")
def index():
    return render_template(
        "base.html", title="Landing Page", arena_settings=arena_settings
    )


@app.route("/control/<int:cageID>")
def realTimer(cageID):
    return render_template(
        "ctimer.html",
        user_screens=user_screens,
        title="Controller",
        cageID=cageID,
        arena_settings=arena_settings,
    )


@app.route("/settings", methods=("GET", "POST"))
def generateSettingsPage():
    if request.method == "GET":
        return render_template("app_settings.html", arena_settings=arena_settings)


@socketio.on("connect")
def base_connection_handler():
    pass


@socketio.on("timer_event")
def handle_message(timer_message):
    print(timer_message)
    emit(
        "timer_event", timer_message["message"], to=f"cage_no_{timer_message['cageID']}"
    )


@socketio.on("timer_bg_event")
def handle_message(timer_bg_data):
    emit("timer_bg_event", timer_bg_data, to=f"cage_no_{timer_bg_data['cageID']}")


@socketio.on("join_cage_request")
def join_cage_handler(request_data: dict):
    if "cage_id" in request_data:
        join_room(f'cage_no_{request_data["cage_id"]}')
        emit(
            "client_joined_room",
            f'cage_no_{request_data["cage_id"]}',
            to=f"cage_no_{request_data['cage_id']}",
        )
        print(f"User SID ({request.sid}) has joined Cage #{request_data['cage_id']}")


@socketio.on("player_ready")
def handle_message(ready_msg: dict):
    print(f"player_ready, {ready_msg} for room {[ctl_rooms for ctl_rooms in rooms()]}")
    emit("control_player_ready_event", ready_msg, to=f"cage_no_{ready_msg['cageID']}")


@socketio.on("player_tapout")
def handle_message(tapout_msg: dict):
    print(
        f"player_tapout, {tapout_msg} for room {[ctl_rooms for ctl_rooms in rooms()]}"
    )
    emit(
        "control_player_tapout_event", tapout_msg, to=f"cage_no_{tapout_msg['cageID']}"
    )


@socketio.on("reset_screen_states")
def handle_message(reset_data):
    emit("reset_screen_states", f"cage_no_{reset_data['cageID']}")


@app.errorhandler(500)
def internal_error(error):
    autoreload = request.args.get("autoreload")
    return render_template(
        "base.html",
        autoreload=autoreload,
        errormsg="Sorry, this page has produced an error while generating.  Please try again in 30s.",
    )


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
