from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, LoginRequest, TokenResponse, ProfileUpdate,WeatherResponse, Coordinates, PostCreate, CommentCreate, CropCreate, CropResponse, CropTaskResponse, AgriculturalEventResponse, CommodityRequest, CommodityPriceResponse
from models import Post, Comment, ServiceProvider, ServiceRequest,Crop, CropTask, AgriculturalEvent
from auth import (
    authenticate_user, create_access_token, get_current_user,
    create_user, get_user_by_username, hash_password
)
from disease_detection import predict_disease
from database import get_db
from datetime import timedelta
from models import User
import requests
from datetime import date
import http.client
import json
import http.client

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 30



#login auth routes
@router.post("/register",tags=["UserLoginAuth"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    create_user(db, user.username, user.email, user.full_name, user.password, user.is_admin)

    return {
        "message": f"User {user.username} successfully registered as {'admin' if user.is_admin else 'regular user'}"}


@router.post("/login", response_model=TokenResponse, tags=["UserLoginAuth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile",tags=["ProfileDetails"])
async def view_profile(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
    }



@router.put("/update-profile",tags=["UserLoginAuth"])
async def update_profile(
        updates: ProfileUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if updates.username:
        if db.query(User).filter(User.username == updates.username).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        user.username = updates.username

    if updates.full_name:
        user.full_name = updates.full_name

    if updates.email:
        if db.query(User).filter(User.email == updates.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = updates.email

    if updates.password:
        user.hashed_password = hash_password(updates.password)

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
        },
    }



@router.delete("/users/{user_id}",tags=["UserManagement"],status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


# Open weather api
@router.post("/weather", response_model=WeatherResponse,tags=["OpenWeatherAPI"])
async def get_weather(coords: Coordinates = Body(...)):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords.lat,
        "longitude": coords.lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code,evapotranspiration,wind_speed_10m,wind_direction_10m,soil_temperature_6cm,soil_moisture_0_to_1cm",
        "timezone": "auto"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve weather data: {response.text}")

    data = response.json()

    return WeatherResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        temperature_2m=data["hourly"]["temperature_2m"],
        relative_humidity_2m=data["hourly"]["relative_humidity_2m"],
        precipitation=data["hourly"]["precipitation"],
        weather_code=data["hourly"]["weather_code"],
        evapotranspiration=data["hourly"]["evapotranspiration"],
        wind_speed_10m=data["hourly"]["wind_speed_10m"],
        wind_direction_10m=data["hourly"]["wind_direction_10m"],
        soil_temperature_6cm=data["hourly"]["soil_temperature_6cm"],
        soil_moisture_0_to_1cm=data["hourly"]["soil_moisture_0_to_1cm"],
    )


#Posts comments routes
@router.post("/posts",tags=["Forum"])
async def create_post(post: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_post = Post(title=post.title, content=post.content, user_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {"message": "Post created successfully", "post": new_post}



@router.delete("/posts/{post_id}",tags=["Forum"])
async def delete_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}



@router.post("/comments",tags=["Forum"])
async def add_comment(comment: CommentCreate, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == comment.post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    new_comment = Comment(content=comment.content, post_id=comment.post_id, user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully", "comment": new_comment}



@router.delete("/comments/{comment_id}",tags=["Forum"])
async def delete_comment(comment_id: int, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully"}



@router.get("/posts",tags=["Forum"])
async def view_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return {"posts": posts}



@router.get("/posts/{post_id}/comments",tags=["Forum"])
async def view_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return {"comments": comments}



@router.put("/posts/{post_id}",tags=["Forum"])
async def update_post(
        post_id: int,
        updates: PostCreate,  # Reusing the `PostCreate` model
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    post.title = updates.title
    post.content = updates.content
    db.commit()
    db.refresh(post)

    return {"message": "Post updated successfully", "post": post}



@router.get("/posts/{post_id}",tags=["Forum"])
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return {"post": post}


# Service routes
@router.post("/services",tags=["Services"])
async def add_service(
        name: str,
        description: str,
        contact_info: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    new_service = ServiceProvider(
        name=name,
        description=description,
        contact_info=contact_info,
        user_id=current_user.id
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return {"message": "Service added successfully", "service": new_service}


@router.get("/services",tags=["Services"])
async def view_services(db: Session = Depends(get_db)):
    services = db.query(ServiceProvider).all()
    return {"services": services}



@router.delete("/services/{service_id}",tags=["Services"])
async def delete_service(
        service_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    service = db.query(ServiceProvider).filter(ServiceProvider.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(service)
    db.commit()

    return {"message": "Service deleted successfully"}



@router.post("/services/{service_id}/request",tags=["Services"])
async def request_service(
        service_id: int,
        description: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    service = db.query(ServiceProvider).filter(ServiceProvider.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    new_request = ServiceRequest(
        description=description,
        service_provider_id=service_id,
        user_id=current_user.id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {"message": "Service requested successfully", "request": new_request}



@router.get("/services/{service_id}/requests",tags=["Services"])
async def view_requests(
        service_id: int,
        db: Session = Depends(get_db)
):
    requests = db.query(ServiceRequest).filter(ServiceRequest.service_provider_id == service_id).all()
    return {"requests": requests}


# ML prediction model route
@router.post("/predict-disease",tags=["PredictionModel"])
async def predict_disease_endpoint(file: UploadFile = File(...)):
    result = predict_disease(file.file)
    return result


# Crops routes
@router.get("/crops", response_model=list[CropResponse],tags=["Crops"])
async def get_crops(db: Session = Depends(get_db)):
    """Fetch all crops."""
    crops = db.query(Crop).all()
    return [CropResponse.model_validate(crop) for crop in crops]


@router.get("/crops/{crop_id}/tasks", response_model=list[CropTaskResponse],tags=["Crops"])
async def get_crop_tasks(crop_id: int, db: Session = Depends(get_db)):
    """Fetch tasks for a specific crop."""
    crop = db.query(Crop).filter(Crop.id == crop_id).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    return [CropTaskResponse.model_validate(task) for task in crop.tasks]


@router.post("/crops", response_model=CropResponse,tags=["Crops"])
async def create_crop(crop: CropCreate, db: Session = Depends(get_db)):
    existing_crop = db.query(Crop).filter(Crop.name == crop.name).first()

    if existing_crop:
        raise HTTPException(status_code=400, detail=f"Crop with name '{crop.name}' already exists.")

    new_crop = Crop(name=crop.name, description=crop.description)
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)

    for task in crop.tasks:
        new_task = CropTask(month=task.month, task=task.task, crop_id=new_crop.id)
        db.add(new_task)

    db.commit()

    return CropResponse.model_validate(new_crop)



@router.delete("/crops/{crop_id}/tasks", status_code=204, tags=["Crops"])
async def delete_crop_tasks(
    crop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete crop tasks."
        )

    crop = db.query(Crop).filter(Crop.id == crop_id).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    db.query(CropTask).filter(CropTask.crop_id == crop_id).delete()
    db.commit()

    return {"message": f"All tasks for crop ID {crop_id} have been deleted successfully"}

# Agricultural calendar
@router.get("/agriculture/calendar", response_model=list[AgriculturalEventResponse], tags=["Agricultural Calendar"])
async def get_agricultural_calendar(db: Session = Depends(get_db)):
    """Fetch all agricultural events along with recommended farming tasks."""
    events = db.query(AgriculturalEvent).all()
    return events


@router.get("/agriculture/calendar/season/{season}", response_model=list[AgriculturalEventResponse], tags=["Agricultural Calendar"])
async def get_events_by_season(season: str, db: Session = Depends(get_db)):
    events = db.query(AgriculturalEvent).filter(AgriculturalEvent.season == season).all()
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for season '{season}'")
    return events


@router.get("/agriculture/calendar/date/{event_date}", response_model=list[AgriculturalEventResponse], tags=["Agricultural Calendar"])
async def get_events_by_date(event_date: date, db: Session = Depends(get_db)):
    events = db.query(AgriculturalEvent).filter(AgriculturalEvent.date == event_date).all()
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for date '{event_date}'")
    return events


@router.get("/agriculture/calendar/category/{category}", response_model=list[AgriculturalEventResponse], tags=["Agricultural Calendar"])
async def get_events_by_category(category: str, db: Session = Depends(get_db)):
    events = db.query(AgriculturalEvent).filter(AgriculturalEvent.category == category).all()
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for category '{category}'")
    return events



#Commodities prices route
COMMODITY_API_KEY = "sk_EBb3274A836943352279a0a8660C540828AaB82839f874cA"

@router.post("/commodity-price", response_model=CommodityPriceResponse, tags=["CommoditiesAPI"])
async def get_commodity_price(request: CommodityRequest = Body(...)):
    conn = http.client.HTTPSConnection("commodities.g.apised.com")

    request_path = f"/v1/latest?symbols={request.commodity.upper()}&base_currency={request.currency.upper()}"

    headers = {
        "x-api-key": COMMODITY_API_KEY
    }

    conn.request("GET", request_path, headers=headers)
    res = conn.getresponse()
    data = res.read()

    try:
        parsed_data = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid response from API")

    print("API Response:", parsed_data)

    commodity_symbol = request.commodity.upper()

    if "data" not in parsed_data or "rates" not in parsed_data["data"] or commodity_symbol not in parsed_data["data"]["rates"]:
        raise HTTPException(status_code=404, detail=f"Commodity '{commodity_symbol}' not found in API response.")

    unit = parsed_data["data"].get("unit", "Unknown")

    return CommodityPriceResponse(
        commodity=commodity_symbol,
        currency=request.currency.upper(),
        price=parsed_data["data"]["rates"][commodity_symbol],
        unit=unit,
        source="APIsed Commodities API"
    )