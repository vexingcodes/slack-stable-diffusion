# ngrok

`ngrok` is a tool for easily exposing local services over the internet.

The `Containerfile` in this directory creates a simple image containing just the
[ngrok](https://ngrok.com) binary and a config file.

This is used to expose the Stable Diffusion Slack entrypoint to the internet.

## Configuration

The config file can be overridden by mounting a different file to `/ngrok.yaml` when starting the
container. The `ngrok` auth token can be provided by specifying the `NGROK_AUTHTOKEN` environment
variable.
