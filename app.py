from http import HTTPStatus
import asyncio
from json import dumps
from datetime import datetime
from functools import wraps

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


def async_debounce(wait):
    def decorator(func):
        task = None

        @wraps(func)
        async def debounced(*args, **kwargs):
            nonlocal task

            async def call_func():
                await asyncio.sleep(wait)
                await func(*args, **kwargs)

            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    print("task canceling error")

            task = asyncio.create_task(call_func())
            return task

        return debounced

    return decorator


@async_debounce(wait=10)
async def process_buffer(user_id):
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
        await asyncio.sleep(10)
        stats = index.describe_index_stats()
        print(stats)
        print(f'Processando mensagens {response}')


@app.post("/message", status_code= HTTPStatus.OK)
async def message(user_id: int, message: str):
    user_buffer.setdefault(user_id, []).append(message)
    process_buffer(user_id)
    return {"status": "Mensagem adicionada"}

