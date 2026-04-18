from typing import cast

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.wrappers import Response

from models.user import User
from services.auth import role_required
from services.db import db

admin_bp: Blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@role_required("admin")
def users() -> str:
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = User.query.order_by(User.created_at.desc()).paginate(page=page, per_app=per_page, error_out=False)
    return render_template("admin/users.html", users=pagination.items, pagination=pagination)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@role_required("admin")
def change_role(user_id: int) -> Response:
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    new_role = request.form.get("role", "").strip()
    if new_role not in ("viewer", "user", "analyst", "admin"):
        flash("Invalid role.", "error")
        return redirect(url_for("admin.users"))

    user.role = new_role
    db.session.commit()
    flash(f"Role updated to {new_role} for {user.email}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/unlock", methods=["POST"])
@role_required("admin")
def unlock_user(user_id: int) -> Response:
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()
    flash(f"Account unlocked for {user.email}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_id: int) -> Response:
    if user_id == cast("User", current_user).id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.email} deleted.", "success")
    return redirect(url_for("admin.users"))
