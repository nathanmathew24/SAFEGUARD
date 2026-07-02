from flask import Blueprint, request, g
from app.utils.errors import error_response
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role
from app.utils.ocr import validate_file
from app.models.user import UserRole
from app.services import extraction_service

upload_bp = Blueprint("upload", __name__)

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@upload_bp.route("/api/upload", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager,
              UserRole.operations_staff, UserRole.viewer)
def upload_file():
    if "file" not in request.files:
        return error_response("MISSING_FILE", "No file in request", 422)

    f = request.files["file"]
    if not f.filename:
        return error_response("MISSING_FILE", "No filename", 422)

    file_bytes = f.read()

    if len(file_bytes) == 0:
        return error_response("INVALID_FILE", "File is empty", 422)

    if len(file_bytes) > _MAX_BYTES:
        return error_response(
            "FILE_TOO_LARGE",
            f"File exceeds 10MB limit (got {len(file_bytes)} bytes)",
            422,
        )

    ok, mime_type, err = validate_file(file_bytes, f.filename)
    if not ok:
        return error_response("INVALID_FILE", err or "File type not allowed", 422)

    company_id = request.form.get("company_id", type=int)
    if not company_id:
        return error_response("VALIDATION_ERROR", "company_id is required", 422)

    try:
        uf = extraction_service.handle_upload(
            file_bytes=file_bytes,
            original_filename=f.filename,
            mime_type=mime_type,
            company_id=company_id,
            user_id=g.current_user.id,
        )
    except Exception as exc:
        return error_response("UPLOAD_FAILED", "Could not store file", 500)

    return {
        "upload_id": uf.id,
        "filename": uf.original_filename,
        "size": uf.file_size,
        "mime_type": uf.mime_type,
    }, 201
