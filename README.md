# Stable Diffusion

Use a [Slack](https://www.slack.com)
[slash-command](https://api.slack.com/interactivity/slash-commands) to generate images using
[Stable Diffusion](https://huggingface.co/spaces/stabilityai/stable-diffusion) and post them to a
Slack channel with image hosting by [Imgur](https://imgur.com/).

This deployment is fully containerized and should work with `docker-compose` and `podman-compose`.
So far, only `podman-compose` has been tested. (Docker may require additional flags to use the GPU?
Podman seems to do it transparently.) Generally you shouldn't have to mess with your network
configuration to get this to work, since everything is tunnelled over [Ngrok](https://ngrok.com/).

So far this has only been tested using rootful Podman. It may be possible to run this using rootless
Podman, but that has not yet been tested. The `stable-diffusion` container currently runs its
process as `root`, but it's likely possible to change that to run as a non-root user. The end goal
would be to be able to run everything in rootless podman where all processes run as non-root from
the container's point of view.

## Prerequisites

This is designed to work on Linux. It may work on other operating systems, but you're on your own.
You must install the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) and ensure it is functional before attempting to use this.

Everything here is [currently] free, but you'll need to set up a few accounts. Namely Slack, Ngrok,
and Imgur.

To create the Slack slash-command you'll need to go to the [Slack API](https://api.slack.com/) page
and create a Slack application. On the "Basic Information" page of the Slack API page for the
application you'll need to gather the `App ID` and `Signing Secret` for use on this. On the Slack
application you'll need to create a slash command for `/str8up`. You won't be able to fill in the
request URL until the server is actually up.

You'll need an [Ngrok](https://ngrok.com/) account to serve the webook for the slash command. When
you sign up, you'll be given an auth token that you'll need to put in a config file here to
authenticate to Ngrok.

Images are uploaded to [Imgur](https://imgur.com/). In order to upload, you need to create an Imgur
application [here](https://api.imgur.com/oauth2/addclient). You can select `Anonymous usage without
user authorization` for the authorization type since we will be uploading images anonymously. Take
note of the client ID and client secret you are given when you create the application, they'll be
needed here to authenticate to Imgur.

## Configuration

The easiest way to configure things is to create a `.env` file in the repository root that looks
like the following:

```
IMGUR_CLIENT_ID=***************
IMGUR_CLIENT_SECRET=****************************************
NGROK_AUTHTOKEN=*************************************************
SLACK_APP_ID=***********
SLACK_SIGNING_SECRET=********************************
```

Replacing the asterisks with the values you got from Slack, Ngrok, and Imgur.

## Operation

Once the `.env` file is in place with the configuration, you can run the following command to build
the containers:

```
podman-compose build
```

You only need to build the containers once initially, and then only whenever the code changes. Once
the containers are built, the system can be started using the following command:

```
podman-compose up --detach
```

This will bring up the `ngrok` and `stable-diffusion` containers. Everything should be ready in a
few seconds after the containers start. Presently, there are some manual steps to finish brining
everything up. First, on the free tier `ngrok` will get a new URL each time it starts. We need to
retreive this URL so we can make it the target URL for the slack slash-command. To find the URL run
the following command:

```
podman-compose logs ngrok | grep "started tunnel" | awk '{print $NF}' | cut -c5-
```

This should print the public URL for the `ngrok` tunnel. Paste this URL into the `Request URL`
section of your Slack slash-command configuration on the Slack API website and click save.
Unfortunately, you must do this every time the `ngrok` container is restarted. It should be
relatively easy to change the code to use a different hosting method if this is unacceptable.

The final step is to install the Slack application in your slack workspace. To do this, go to the
`Install App` page of the Slack API website, and click the button to install it to the workspace.

At this point, users of your Slack workspace should be able to run commands like:

```
/str8up a cute squid squirting ink onto a canvas
```

And have it be replaced with an AI-generated image relatively quickly!

## Plans

- Download the official weights. Right now it's using some random URL I found. I think this download
  needs a token, so it's not non-trivial, but probably pretty easy to do.
- Tuning and ensuring that the Stable Diffusion output is good.
- Guard against multiple images being generated simultaneously. This is untested, but I would expect
  it to fail due to being out of GPU memory.
- Allow non-ngrok hosting and local image hosting. This could be attained using nginx and saving the
  image files locally.
