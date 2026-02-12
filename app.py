from http import HTTPStatus
import asyncio
from datetime import datetime

from models import Message

from fastapi import FastAPI

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
pc: str = os.environ.get("PINECONE_KEY")

app = FastAPI()

user_buffer = {}
user_id = 1

async def process_buffer(user_id):
    await asyncio.sleep(40)
    messages = user_buffer.pop(user_id, [])
    if messages:
        print(f'Processando mensagens {messages}')


@app.post("/message", status_code= HTTPStatus.OK)
async def message(user_id: str, message: str):
    user_buffer.setdefault(user_id, []).append(message)
    asyncio.create_task(process_buffer(user_id))
    return {"status": "Mensagem adicionada"}

