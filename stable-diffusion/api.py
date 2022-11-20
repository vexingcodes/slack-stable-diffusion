from hashlib import sha256
from hmac import new as hmac_new
from os import environ
from time import time
from typing import Union

from fastapi import BackgroundTasks, Body, FastAPI, Form, Header, HTTPException, Request, status
from fastapi.logger import logger
from imgurpython import ImgurClient
from requests import post

from gen import gen

# Extract configuration from the environment.
imgur_client_id = environ["IMGUR_CLIENT_ID"]
imgur_client_secret = environ["IMGUR_CLIENT_SECRET"]
slack_app_id = environ["SLACK_APP_ID"]
slack_signing_secret = environ["SLACK_SIGNING_SECRET"]

# Initialize services.
imgur = ImgurClient(imgur_client_id, imgur_client_secret)
app = FastAPI()

@app.post("/")
async def slack(
  request: Request,
  background_tasks: BackgroundTasks,
  body: bytes = Body(...),
  x_slack_request_timestamp: Union[str, None] = Header(default=None),
  x_slack_signature: Union[str, None] = Header(default=None),
):
  # Detect potential replay attacks.
  try:
    timestamp = int(x_slack_request_timestamp)
  except (ValueError, TypeError):
    logger.error(f"Could not parse {timestamp=}")
    raise HTTPException(status.HTTP_400_BAD_REQUEST)
  now = time()
  if abs(now - timestamp) > 60:
    logger.error(f"Possible replay attack {timestamp=} {now=}")
    raise HTTPException(status.HTTP_400_BAD_REQUEST)

  # Check the signature to authenticate the request came from Slack.
  signature = hmac_new(
    slack_signing_secret.encode(),
    f"v0:{timestamp}:{body.decode()}".encode(),
    sha256
  )
  if not x_slack_signature == f"v0={signature.hexdigest()}":
    logger.error(f"Unable to validate signature")
    raise HTTPException(status.HTTP_400_BAD_REQUEST)

  data = await request.form()

  # Ensure the app ID in the request matches the app ID we think we are.
  got_app_id = data["api_app_id"]
  if not got_app_id == slack_app_id:
    logger.error(f"Unexpected app ID {slack_app_id=} {got_app_id=}")
    raise HTTPException(status.HTTP_400_BAD_REQUEST)

  # This is a valid request. Schedule background processing and return status immediately.
  background_tasks.add_task(
    process_request,
    command = data["command"],
    text = data["text"], 
    response_url = data["response_url"],
    user_id = data["user_id"],
  )

  return { "response_type": "ephermeral", "text": "Processing..." }

def process_request(command: str, text: str, response_url: str, user_id: str):
  logger.info("Generating image...")
  gen(text)
  logger.info("Uploading to imgur...")
  image_url = imgur.upload_from_path("/tmp/foo.png")["link"]

  logger.info("Returning response...")
  result = post(response_url, json={
    "response_type": "in_channel",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"User: <@{user_id}>\nPrompt: {text}",
        },
      },
      {
        "type": "image",
        "image_url": image_url,
        "alt_text": f"{text}",
      },
    ]
  })

  if not result.ok:
    logger.error(f"Error posting response {result=}")
  else:
    logger.info("Request complete!")
