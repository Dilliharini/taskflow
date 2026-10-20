import uuid
import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.realtime import project_connections
from app.core.security import decode_access_token
from app.models import ProjectMember, User

router = APIRouter()


@router.websocket("/projects/{project_id}")
async def project_updates(websocket: WebSocket, project_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    # Native browser WebSockets do not support custom Authorization headers. The
    # client sends its bearer token in the first frame, never in the URL.
    await websocket.accept()
    try:
        auth_frame = await websocket.receive_json()
    except (WebSocketDisconnect, ValueError):
        return
    token = auth_frame.get("access_token") if isinstance(auth_frame, dict) and auth_frame.get("type") == "auth" else None
    if not isinstance(token, str) or not token:
        await websocket.close(code=4401, reason="Authentication required")
        return
    try:
        claims = decode_access_token(token)
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        await websocket.close(code=4401, reason="Invalid authentication")
        return

    try:
        user = db.get(User, user_id)
        membership = db.scalar(select(ProjectMember.id).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ))
    except SQLAlchemyError:
        db.rollback()
        await websocket.close(code=1011, reason="Unable to authorize project access")
        return
    if user is None or not user.is_active or membership is None:
        await websocket.close(code=4403, reason="Project access denied")
        return

    websocket.taskflow_user_id = str(user_id)
    await project_connections.register(str(project_id), websocket)
    try:
        while True:
            # Clients send only keepalive messages; server events are server-authored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await project_connections.disconnect(str(project_id), websocket)