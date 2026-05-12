from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/privacy-policy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy_page():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="es">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Politica de privacidad | Apitool</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }
              main { max-width: 860px; margin: 0 auto; padding: 40px 20px 60px; }
              .card { background: #ffffff; border-radius: 16px; padding: 28px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
              h1, h2 { color: #111827; }
              h1 { margin-top: 0; }
              p, li { line-height: 1.65; color: #334155; }
              ul { padding-left: 20px; }
              a { color: #b45309; }
            </style>
          </head>
          <body>
            <main>
              <div class="card">
                <h1>Politica de privacidad</h1>
                <p>Apitool ayuda a gestionar apiarios, colmenas, visitas, tareas, dispositivos y suscripciones. Esta politica explica de forma resumida que datos usamos y con que finalidad.</p>

                <h2>Datos que podemos procesar</h2>
                <ul>
                  <li>Datos de cuenta: nombre, apellido, correo electronico y credenciales de acceso.</li>
                  <li>Datos operativos: apiarios, colmenas, visitas, tareas, historial, imagenes y configuraciones.</li>
                  <li>Datos tecnicos: informacion del dispositivo, version de la app, plataforma y tokens de notificaciones.</li>
                  <li>Permisos del dispositivo: ubicacion, camara, almacenamiento y notificaciones, segun las funciones que uses.</li>
                  <li>Datos de suscripcion: estado de plan, vencimientos e identificadores tecnicos asociados a RevenueCat o tiendas de aplicaciones.</li>
                </ul>

                <h2>Para que usamos los datos</h2>
                <ul>
                  <li>Crear y administrar tu cuenta.</li>
                  <li>Prestar las funciones principales de la aplicacion.</li>
                  <li>Sincronizar suscripciones y habilitar funcionalidades premium.</li>
                  <li>Enviar notificaciones operativas cuando corresponda.</li>
                  <li>Mejorar seguridad, soporte, estabilidad y prevencion de abuso.</li>
                </ul>

                <h2>Comparticion y terceros</h2>
                <p>Podemos apoyarnos en proveedores tecnicos para autenticacion, almacenamiento, hosting, notificaciones y suscripciones. No vendemos tus datos personales.</p>

                <h2>Retencion y eliminacion</h2>
                <p>Conservamos los datos mientras tu cuenta este activa o mientras sea necesario para operar el servicio y cumplir obligaciones tecnicas o legales. Puedes solicitar la eliminacion de tu cuenta desde la app o desde el recurso web de eliminacion de cuenta.</p>

                <h2>Tus opciones</h2>
                <ul>
                  <li>Actualizar tu perfil desde la app.</li>
                  <li>Gestionar dispositivos y cerrar sesion.</li>
                  <li>Solicitar eliminacion de cuenta en <a href="/users/account-deletion">/users/account-deletion</a>.</li>
                </ul>

                <h2>Contacto</h2>
                <p>Si necesitas ayuda o tienes dudas sobre privacidad, usa la pagina de soporte disponible en <a href="/legal/support">/legal/support</a>.</p>
              </div>
            </main>
          </body>
        </html>
        """
    )


@router.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support_page():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="es">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Soporte | Apitool</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }
              main { max-width: 860px; margin: 0 auto; padding: 40px 20px 60px; }
              .card { background: #ffffff; border-radius: 16px; padding: 28px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
              h1 { margin-top: 0; }
              p, li { line-height: 1.65; color: #334155; }
              a { color: #b45309; }
            </style>
          </head>
          <body>
            <main>
              <div class="card">
                <h1>Soporte de Apitool</h1>
                <p>Si necesitas ayuda con acceso, suscripciones, errores o datos de tu cuenta, puedes usar estos canales:</p>
                <ul>
                  <li>Eliminacion de cuenta: <a href="/users/account-deletion">/users/account-deletion</a></li>
                  <li>Politica de privacidad: <a href="/legal/privacy-policy">/legal/privacy-policy</a></li>
                </ul>
                <p>Al escribirnos, incluye el correo de tu cuenta, plataforma y una breve descripcion del problema para agilizar la respuesta.</p>
              </div>
            </main>
          </body>
        </html>
        """
    )
