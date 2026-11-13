from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

# Инициализация приложения FastAPI с подробным описанием
app = FastAPI(
    title="Transport Service API",
    description="Микросервис для управления транспортными маршрутами. "
                "Реализован REST API с поддержкой OpenAPI 3.0.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==========================================
# 1. МОДЕЛИ ДАННЫХ (DTO) с примерами
# ==========================================
class RouteBase(BaseModel):
    name: str = Field(
        ...,
        description="Номер или название маршрута",
        examples=["№ 101"]
    )
    start_point: str = Field(
        ...,
        description="Начальная точка маршрута",
        examples=["Центральный вокзал"]
    )
    end_point: str = Field(
        ...,
        description="Конечная точка маршрута",
        examples=["Аэропорт"]
    )
    distance_km: float = Field(
        ...,
        description="Протяженность маршрута в километрах (должна быть > 0)",
        examples=[25.5]
    )

class RouteCreate(RouteBase):
    """Модель для создания нового маршрута (POST-запрос)."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "№ 101",
                    "start_point": "Центральный вокзал",
                    "end_point": "Аэропорт",
                    "distance_km": 25.5
                }
            ]
        }
    }

class RouteResponse(RouteBase):
    """Модель ответа с идентификатором маршрута."""
    id: int = Field(..., description="Уникальный идентификатор маршрута", examples=[1])

class MessageResponse(BaseModel):
    """Модель для сообщений об успехе/ошибке."""
    message: str = Field(..., examples=["Маршрут 1 успешно удален"])

class ErrorResponse(BaseModel):
    """Модель ошибки."""
    detail: str = Field(..., examples=["Маршрут с указанным ID не найден"])

# ==========================================
# 2. IN-MEMORY ХРАНИЛИЩЕ (Заглушка БД)
# ==========================================
db: List[RouteResponse] = []
current_id = 1

# ==========================================
# 3. REST API ENDPOINTS
# ==========================================

# GET /api/v1/routes/ — получение списка объектов
@app.get(
    "/api/v1/routes/",
    response_model=List[RouteResponse],
    status_code=status.HTTP_200_OK,
    tags=["Routes"],
    summary="Получить список всех маршрутов",
    description="Возвращает массив всех сохранённых маршрутов. Если маршрутов нет — вернёт пустой массив.",
    responses={
        200: {"description": "Успешный запрос. Список маршрутов."}
    }
)
async def get_routes():
    return db


# GET /api/v1/routes/{id} — получение детальной информации
@app.get(
    "/api/v1/routes/{route_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routes"],
    summary="Получить маршрут по ID",
    description="Возвращает детальную информацию о маршруте по его уникальному идентификатору.",
    responses={
        200: {"description": "Успешный запрос. Данные маршрута."},
        404: {"description": "Маршрут не найден", "model": ErrorResponse}
    }
)
async def get_route(route_id: int):
    for route in db:
        if route.id == route_id:
            return route
    raise HTTPException(status_code=404, detail="Маршрут с указанным ID не найден")


# POST /api/v1/routes/ — создание нового объекта
@app.post(
    "/api/v1/routes/",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Routes"],
    summary="Создать новый маршрут",
    description="Создаёт новый маршрут и возвращает его с присвоенным ID.",
    responses={
        201: {"description": "Маршрут успешно создан."},
        400: {"description": "Некорректные данные (например, distance_km <= 0)", "model": ErrorResponse},
        422: {"description": "Ошибка валидации JSON (неверный тип данных)"}
    }
)
async def create_route(route: RouteCreate):
    global current_id

    if route.distance_km <= 0:
        raise HTTPException(
            status_code=400,
            detail="Протяженность маршрута должна быть больше 0"
        )

    new_route = RouteResponse(id=current_id, **route.model_dump())
    db.append(new_route)
    current_id += 1
    return new_route


# DELETE /api/v1/routes/{id} — удаление объекта
@app.delete(
    "/api/v1/routes/{route_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routes"],
    summary="Удалить маршрут по ID",
    description="Удаляет маршрут по его идентификатору. Повторное удаление вернёт 404.",
    responses={
        200: {"description": "Маршрут успешно удалён."},
        404: {"description": "Маршрут не найден", "model": ErrorResponse}
    }
)
async def delete_route(route_id: int):
    for i, route in enumerate(db):
        if route.id == route_id:
            db.pop(i)
            return {"message": f"Маршрут {route_id} успешно удален"}
    raise HTTPException(status_code=404, detail="Маршрут с указанным ID не найден")