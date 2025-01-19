from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from routes import router

app = FastAPI(
    title="AgriCal",
    description="API for managing Tunisia's agricultural calendar, weather, and commodity pricing.",
    version="1.0.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@app.get("/secure-route", dependencies=[Depends(oauth2_scheme)])
async def secure_route():
    """Test route that requires authentication"""
    return {"message": "You are authenticated!"}


app.include_router(router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/login",
                    "scopes": {}
                }
            }
        }
    }

    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi