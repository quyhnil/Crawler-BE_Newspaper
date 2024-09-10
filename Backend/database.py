import sqlite3
from sqlite3 import Connection
from typing import Dict, List, Tuple

from fastapi import HTTPException

from models import NewspaperItem

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import tweepy

genai.configure(api_key="AIzaSyCVgvyy7kMXehV4jowGDLXLyqfU7Ca8MTM")

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 1000,
  "response_mime_type": "text/plain",
}


twitter_client = None

def initialize_twitter_client(api_key, api_secret, bearer_token, access_token, access_token_secret):
    global twitter_client
    twitter_client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)

def post_to_twitter(content: str) -> Dict[str, bool]:
    if twitter_client is None:
        raise HTTPException(status_code=400, detail="Twitter client not initialized. Please set API keys first.")
    try:
        twitter_client.create_tweet(text=content)
        return {"success": True}
    except Exception as e:
        print(f"Error posting to Twitter: {e}")
        return {"success": False}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=(
       'あなたは、ソーシャル ネットワークに投稿するために新聞を読んで要約している人です。'
    ),
)

scoring = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=(
    'あなたの任務は、AI関連性、有用性、理解のしやすさという3つの基準でグループ内の各タイトルを評価することです。各タイトルについて、3つの基準の合計スコアを算出し、10点満点で平均スコアを計算してください。結果として、各タイトルの平均スコアのみをカンマで区切って返してください。'
)

)

suggestion = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=(
        '結果はテキストのみで返してください。'
    ),
)


def score_titles(titles: List[str]):
    chat_session = scoring.start_chat(history=[])

    titles_text = "\n".join(titles)

    response = chat_session.send_message(
        titles_text,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    ).text
    return response

def get_newspapers(
    connection: Connection, limit: int = 5, page: int = 0
) -> List[Dict]:
    offset = limit * page
    cur = connection.cursor()
    cur.execute(
        """
        SELECT *
        FROM articles
        ORDER BY time DESC
        LIMIT :limit
        OFFSET :offset
        """,
        {
            "limit": limit,
            "offset": offset,
        },
    )

    newspapers = [dict(row) for row in cur.fetchall()]
    
    for newspaper in newspapers:
        if newspaper['score'] is None or newspaper['summary'] is None:
            title = newspaper['title']
            content = newspaper['content']
            
            score = float(score_titles([title]).split(",")[0])
            summary = get_summary([content])[0]
            
            cur.execute(
                """
                UPDATE articles
                SET score = :score, summary = :summary
                WHERE id = :id
                """,
                {
                    "score": score,
                    "summary": summary,
                    "id": newspaper['id']
                },
            )
            connection.commit()
            newspaper['score'] = score
            newspaper['summary'] = summary
    
    return newspapers

def get_combined_summary(content: str) -> List[str]:
    chat_session = model.start_chat(
        history=[
        ]
    )
    prompt = "以下の10個の記事をそれぞれ要約してください。各要約は1~2文で簡潔にまとめてください。要約と要約の間に '---' を入れてください。\n\n" + content
    response = chat_session.send_message(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    return response.text.split("---")

def get_summary(contents: List[str]):
    
    if contents is None:
        raise HTTPException(status_code=404, detail="Article not found")
    chat_session = model.start_chat(
        history=[
        ]
    )
    summaries = []
    for content in contents:
        prompt = "以下の文章を要約してください。\n\n" + content
        response = chat_session.send_message(prompt)
        summaries.append(response.text)
    
    return summaries

def edit_summary_with_gemini(summary: str, instruction: str) -> str:
    prompt = f"現在の要約は以下の通りです:{summary}この要約を次の指示に従って修正してください: {instruction}"
    chat_session = suggestion.start_chat(
        history=[
        ]
    )
    response = chat_session.send_message(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    return response.text

def decrease_summary_with_gemini(text: str, reduction: int) -> str:
    chat_session = model.start_chat(
        history=[
        ]
    )
    prompt = (
        f"以下のテキストを{reduction}%減らして要約してください:\n\n{text}\n\n"
        "要約には重要なポイントを含め、簡潔にしてください。"
    )
    response = chat_session.send_message(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    return response.text

def increase_summary_with_gemini(summary_text: str, expansion: int) -> str:
    chat_session = model.start_chat(
        history=[
        ]
    )
    prompt = (
        f"以下は記事の要約です:\n\n{summary_text}\n\n"
        f"この要約を{expansion}%拡張してください。\n\n"
        "拡張された要約には、明確さと一貫性を保ってください。"

    )
    response = chat_session.send_message(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    return response.text
