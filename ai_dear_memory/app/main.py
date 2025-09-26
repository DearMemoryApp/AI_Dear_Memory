from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import router

app = FastAPI(title="dear-memory", version="0.1.0")

# Define allowed origins
origins = [
    "*",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify the allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Test root endpoint
@app.get("/")
async def root():
    return {"message": "Dear Memory fastAPI live"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = (
        "Invalid JSON format of request body."
        if any(error["type"] == "json_invalid" for error in exc.errors())
        else "Invalid request body."
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": status.HTTP_400_BAD_REQUEST,
            "error": "Validation Error",
            "message": message,
        },
    )


app.include_router(router)
