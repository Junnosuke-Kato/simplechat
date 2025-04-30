# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
import urllib.request


API_URL = os.environ.get("LLM_API_URL", "https://your-ngrok-url.ngrok.io/generate")  # 環境変数からURLを取得
MAX_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", 512))

def lambda_handler(event, context):
    try:
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        # 過去のメッセージをプロンプトに連結
        history_text = ""
        for msg in conversation_history:
            role = msg["role"]
            content = msg["content"]
            prefix = "User:" if role == "user" else "Assistant:"
            history_text += f"{prefix} {content}\n"
        prompt = f"{history_text}User: {message}\nAssistant:"

        # FastAPIに送るJSONリクエストデータ
        request_data = {
            "prompt": prompt,
            "max_new_tokens": MAX_TOKENS,
            "temperature": 0.7,
            "top_p": 0.9
        }
        json_data = json.dumps(request_data).encode("utf-8")

        # POSTリクエストの準備
        req = urllib.request.Request(
            API_URL,
            data=json_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # API呼び出し
        with urllib.request.urlopen(req) as res:
            res_body = res.read().decode("utf-8")
            res_json = json.loads(res_body)

        # 応答取得
        assistant_response = res_json.get("generated_text", "（応答がありません）")

        # 新しい会話履歴を構築
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as e:
        print(f"Error calling FastAPI: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }

