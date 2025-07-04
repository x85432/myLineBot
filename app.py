# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import asyncio
from inspect import signature
import os
import sys
from dotenv import load_dotenv
from fastapi import Request, FastAPI, HTTPException
from contextlib import asynccontextmanager
from google import genai

from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    StickerMessage,
    PushMessageRequest
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent
)
# Configurations
load_dotenv(dotenv_path='.env', override=True)
channel_secret = os.getenv('CHANNEL_SECRET', None)
channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN', None)
server_platform = os.getenv('SERVER_PLATFORM', 'ngrok')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", None))
chat = client.chats.create(model="gemini-2.0-flash")


if channel_secret is None:
    print('Specify CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

configuration = Configuration(
    access_token=channel_access_token
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 這裡是 startup 階段
    user_id = os.getenv('USER_ID')
    if user_id:
        try:
            await line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=f"LINE bot 已經重新啟動在 {server_platform}")]
                )
            )
            print("Startup notification sent to owner.")
        except Exception as e:
            print(f"Failed to send startup notification: {e}")

    yield  # <-- 這裡是分隔 startup 和 shutdown

    # 這裡是 shutdown 階段
    print("FastAPI app is shutting down...")


# startup
app = FastAPI(lifespan=lifespan)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

user_chats = {}  # 儲存每個使用者的獨立 chat session


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if isinstance(event.message, TextMessageContent):
            user_input = event.message.text
            user_id = event.source.user_id

            # 如果是第一次對話，幫使用者創建獨立 chat session
            if user_id not in user_chats:
                user_chats[user_id] = client.chats.create(model="gemini-2.0-flash")
                print(f"Created new chat session for user: {user_id}")

            # 從使用者的專屬 chat session 取得對話回應
            chat = user_chats[user_id]
            response = chat.send_message(user_input)
            response_text = response.text

            # 把 AI 回應回傳給使用者
            await line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response_text)]
                )
            )
        elif isinstance(event.message, StickerMessageContent):
            # 使用者傳貼圖
            bunny1 = StickerMessage(
                            package_id="11537",  # 貼圖包 ID
                            sticker_id="52002742"  # 貼圖 ID
                        )
            bunny2 = StickerMessage(
                            package_id="11537",  # 貼圖包 ID
                            sticker_id="52002745"  # 貼圖 ID
                        )
            user_id = event.source.user_id
            await line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[bunny1]
                )
            )
            await asyncio.sleep(1)

            await line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[bunny2]
                )
            )
            await asyncio.sleep(0.5)

            await line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text="我也會貼圖喔！")]
                )
            )

    return 'OK'
