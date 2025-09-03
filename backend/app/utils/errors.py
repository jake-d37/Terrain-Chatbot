from flask import jsonify


class ToolError(Exception):
    pass


def register_error_handlers(app):
    @app.errorhandler(ToolError)
    def _tool_err(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(404)
    def _404(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(Exception)
    def _any(e):
        # TODO: log error
        return jsonify({"error": "internal error"}), 500
