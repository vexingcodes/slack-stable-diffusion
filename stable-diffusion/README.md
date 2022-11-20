# Stable Diffusion

A container image that hosts a simple slack slash-command API to generate images on demand using
Stable Diffusion. Images are uploaded to Imgur.

The slash command is assumed to be named `str8up`.

## Configuration

All configuration is performed through environment variables. The following environment variables
must be supplied to the container:

- `IMGUR_CLIENT_ID` -- The client ID for your Imgur application.
- `IMGUR_CLIENT_SECRET` -- The client secret for your Imgur application.
- `SLACK_APP_ID` -- The app ID for your Slack application.
- `SLACK_SIGNING_SECRET` -- The signing secret for your Slack application.

## Files

- `api.py` -- Deals with receiving and validating the Slack slash command. Coordinates image
  generation, uploading, and responding to Slack once the upload completes.
- `Containerfile` -- Builds the image. This has to download a large amount of information, so it
  will likely take a long time to complete.
- `gen.py` -- Deals with Stable Diffusion. Loads Stable Diffusion on import, and exposes a `gen`
  function to generate images.
