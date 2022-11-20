import os
import sys
import cv2
import torch
import numpy as np
from omegaconf import OmegaConf
from PIL import Image
from tqdm import tqdm, trange
from einops import rearrange
from pytorch_lightning import seed_everything
from torch import autocast
from ldm.util import instantiate_from_config
from ldm.models.diffusion.ddim import DDIMSampler

from fastapi.logger import logger

logger.error("Initializing Stable-Diffusion...")
seed_everything(42)
config = OmegaConf.load("/opt/stable-diffusion/configs/stable-diffusion/v1-inference.yaml")
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
pl_sd = torch.load("/opt/stable-diffusion/models/ldm/stable-diffusion-v1/model.ckpt", map_location="cpu")
model = instantiate_from_config(config.model)
model.load_state_dict(pl_sd["state_dict"], strict=False)
model.cuda()
model.eval()
model = model.to(device)
sampler = DDIMSampler(model)
batch_size = 1
logger.error("Stable-Diffusion initialization complete!")

def gen(prompt: str):
    data = [1 * [prompt]]
    with torch.no_grad(), autocast("cuda"), model.ema_scope():
        all_samples = list()
        for prompts in tqdm(data, desc="data"):
            uc = model.get_learned_conditioning(1 * [""])
            if isinstance(prompts, tuple):
                prompts = list(prompts)
            c = model.get_learned_conditioning(prompts)
            # 4 is latent channels
            # 8 is downsampling factor
            # 384 (first is height) (second is width)
            shape = [4, 384 // 8, 384 // 8]
            samples_ddim, _ = sampler.sample(S=50,
                                             conditioning=c,
                                             batch_size=1,
                                             shape=shape,
                                             verbose=False,
                                             unconditional_guidance_scale=7.5,
                                             unconditional_conditioning=uc,
                                             eta=0.0,
                                             x_T=None)

            x_samples_ddim = model.decode_first_stage(samples_ddim)
            x_samples_ddim = torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0)
            x_samples_ddim = x_samples_ddim.cpu().permute(0, 2, 3, 1).numpy()
            x_checked_image_torch = torch.from_numpy(x_samples_ddim).permute(0, 3, 1, 2)

            for x_sample in x_checked_image_torch:
                x_sample = 255. * rearrange(x_sample.cpu().numpy(), 'c h w -> h w c')
                img = Image.fromarray(x_sample.astype(np.uint8))
                img.save("/tmp/foo.png")
