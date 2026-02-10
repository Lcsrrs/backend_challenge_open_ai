from http import HTTPStatus

from models import Message

from fastapi import FastAPI

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

@app.get("/", status_code= HTTPStatus.OK, response_model = Message)
def index():
    return {'message': 'hello world'}

