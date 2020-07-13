from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from feature_extractor.visualizer.auth import login_required
from feature_extractor.visualizer.db import get_db
from flask import current_app

bp = Blueprint("visualizer", __name__)


@bp.route("/")
@login_required
def index():
 # TODO: Lee config
 # TODO: Carga input plugin y genera variable p_data que se pasa al core_plugin para que lo pase a su template
    """Show the mse plot for the last training process, also the last validation plot and a list of validation stats."""
    print ("current_app.config['P_CONFIG'] = ", current_app.config['P_CONFIG'])
    p_config = current_app.config['P_CONFIG']
    db = get_db()
    training_progress = db.execute(
        "SELECT *"
        " FROM training_progress t JOIN process p ON t.process_id = p.id"
        " ORDER BY created DESC"
    ).fetchall()
    validation_plots = db.execute(
        "SELECT *"
        " FROM validation_plots t JOIN process p ON t.process_id = p.id"
        " ORDER BY created DESC"
    ).fetchall()
    validation_stats = db.execute(
        "SELECT *"
        " FROM validation_stats t JOIN process p ON t.process_id = p.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("visualizer/index.html", p_config = p_config)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("visualizer.index"))

    return render_template("visualizer/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("visualizer.index"))

    return render_template("visualizer/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("visualizer.index"))
