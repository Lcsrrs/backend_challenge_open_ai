from http import HTTPStatus
import asyncio
import time
from json import dumps
from datetime import datetime

from fastapi import FastAPI

import os
from supabase import create_client, Client
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

pc: str = Pinecone(os.environ.get("PINECONE_KEY"))
index = pc.Index("backend-challenge")

app = FastAPI()

user_buffer = {}

async def process_buffer(user_id):
    await asyncio.sleep(5)
    messages = user_buffer.pop(user_id, [])
    if messages:
        #supabase
        dt = datetime.now()
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        dt_json = dumps(dt_str)
        response = supabase.table("Memory").insert({"user_id": user_id, "message": messages, "time_stamp": dt_json}).execute()

        #pinecone
        upsert_data = [{"_id": f'message{i}', "__default__": text} for i, text in enumerate(messages, start=1)]
        index.upsert_records(user_id, upsert_data)
        time.sleep(10)
        stats = index.describe_index_stats()
        print(stats)
        print(f'Processando mensagens {response}')


@app.post("/message", status_code= HTTPStatus.OK)
async def message(user_id: int, message: str):
    user_buffer.setdefault(user_id, []).append(message)
    asyncio.create_task(process_buffer(user_id))
    return {"status": "Mensagem adicionada"}

