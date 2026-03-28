from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import score, rag, parts

app = FastAPI(title="FixIt Buddy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fixit-buddy-97w5.vercel.app",
        "http://localhost:3000",]

    ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(score.router, prefix="/api/score", tags=["Score"])
app.include_router(rag.router,   prefix="/api/rag",   tags=["RAG"])
app.include_router(parts.router, prefix="/api/parts", tags=["Parts"])

@app.get("/")
def root():
    return {"status": "FixIt Buddy API is running 🔧"}
