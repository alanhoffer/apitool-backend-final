from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import DeleteAccountRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    delete_request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Elimina la cuenta autenticada y los datos asociados.
    """
    user_service = UserService(db)
    auth_service = AuthService(db)

    user_service.validate_delete_account(current_user, delete_request.currentPassword, auth_service)
    success = user_service.delete_user(current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "Cuenta eliminada exitosamente"}


@router.get("/account-deletion", response_class=HTMLResponse, include_in_schema=False)
async def account_deletion_page():
    """
    Recurso web pÃºblico para la eliminaciÃ³n de cuenta solicitado por Google Play.
    """
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="es">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Eliminar cuenta | Apitool</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }
              main { max-width: 720px; margin: 0 auto; padding: 40px 20px; }
              .card { background: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
              h1 { margin-top: 0; }
              p { line-height: 1.55; }
              label { display: block; margin: 16px 0 8px; font-weight: 600; }
              input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 10px; box-sizing: border-box; }
              button { margin-top: 20px; background: #b45309; color: #ffffff; border: none; border-radius: 10px; padding: 12px 16px; font-weight: 700; cursor: pointer; }
              .note { margin-top: 16px; font-size: 14px; color: #475569; }
            </style>
          </head>
          <body>
            <main>
              <div class="card">
                <h1>Solicitud de eliminacion de cuenta</h1>
                <p>Si ya no deseas usar Apitool, puedes eliminar tu cuenta y los datos asociados completando este formulario.</p>
                <p>Si estas dentro de la app, tambien puedes hacerlo desde Perfil &gt; Seguridad &gt; Eliminar cuenta.</p>
                <form method="post" action="/users/account-deletion">
                  <label for="email">Correo electronico</label>
                  <input id="email" name="email" type="email" required />
                  <label for="password">Contrasena actual</label>
                  <input id="password" name="password" type="password" required minlength="7" />
                  <button type="submit">Eliminar mi cuenta</button>
                </form>
                <p class="note">Esta accion es permanente y elimina tambien los datos asociados a tu cuenta.</p>
              </div>
            </main>
          </body>
        </html>
        """
    )


@router.post("/account-deletion", response_class=HTMLResponse, include_in_schema=False)
async def account_deletion_request(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Permite solicitar la eliminaciÃ³n de cuenta desde un recurso web externo.
    """
    user_service = UserService(db)
    auth_service = AuthService(db)
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_service.validate_delete_account(user, password, auth_service)
    user_service.delete_user(user.id)

    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="es">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Cuenta eliminada | Apitool</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }
              main { max-width: 720px; margin: 0 auto; padding: 40px 20px; }
              .card { background: #ffffff; border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
            </style>
          </head>
          <body>
            <main>
              <div class="card">
                <h1>Cuenta eliminada</h1>
                <p>La cuenta y los datos asociados fueron eliminados correctamente.</p>
              </div>
            </main>
          </body>
        </html>
        """
    )
