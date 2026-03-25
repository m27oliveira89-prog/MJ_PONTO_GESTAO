from flask import Flask, redirect, render_template, request, session, url_for

from config import Config
from controllers.admin_controller import admin_bp
from controllers.auth_controller import auth_bp
from controllers.exportacao_controller import exportacao_bp
from controllers.funcionarios_controller import funcionarios_bp
from controllers.historico_controller import historico_bp
from controllers.home_controller import home_bp
from controllers.ponto_controller import ponto_bp
from controllers.relatorios_controller import relatorios_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(exportacao_bp)
    app.register_blueprint(funcionarios_bp)
    app.register_blueprint(historico_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(ponto_bp)
    app.register_blueprint(relatorios_bp)

    @app.route("/admin/area")
    def admin_access():
        current_user = session.get("user")

        if not current_user:
            return redirect(url_for("auth.login", mode="admin"))

        if current_user.get("role") != "admin":
            return redirect(url_for("home.index"))

        return render_template("admin.html", current_user=current_user)

    @app.before_request
    def require_login():
        public_endpoints = {"auth.login", "auth.logout"}

        if request.endpoint is None:
            return None

        if request.endpoint.startswith("static"):
            return None

        if request.endpoint in public_endpoints:
            return None

        if not session.get("user"):
            return redirect(url_for("auth.login"))

        return None

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
