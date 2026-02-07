from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ame.config import load_config
from ame.orchestrator import Orchestrator
from ame.motor_openai import OpenAIMotor
from ame.registry import JsonlRegistry

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Nemosine Nous — PoC + AME", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# AME wiring (core loop)
# -----------------------------
CONFIG = load_config()
REGISTRY = JsonlRegistry(path=os.path.join(os.path.dirname(__file__), "runtime", "cycles.jsonl"))
MOTOR = OpenAIMotor(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    model=os.getenv("OPENAI_MODEL", CONFIG.model),
)
ORCH = Orchestrator(config=CONFIG, motor=MOTOR, registry=REGISTRY)


class Message(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True, "version": app.version}


@app.get("/ame/config")
def get_config():
    # Configuração é EXTERNA ao motor e inspecionável (TR-004)
    return CONFIG.to_public_dict()


@app.get("/ame/last")
def last_cycle():
    last = REGISTRY.read_last()
    return {"last": last}


@app.post("/chat")
def chat(message: Message):
    if not message.text or not message.text.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    if not MOTOR.is_configured():
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    result = ORCH.run(user_text=message.text)
    return {"reply": result.reply, "cycle_id": result.cycle_id}
