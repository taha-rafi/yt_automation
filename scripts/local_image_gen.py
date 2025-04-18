import torch
from diffusers import StableDiffusionPipeline

def generate_image(prompt, output_path, model_id="runwayml/stable-diffusion-v1-5", device=None):
    """
    Generate an image from a prompt using a local Stable Diffusion pipeline.
    Args:
        prompt (str): The text prompt to generate the image.
        output_path (str): Where to save the generated image.
        model_id (str): Hugging Face model ID.
        device (str): 'cuda' or 'cpu'. If None, auto-detect.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if device=="cuda" else torch.float32)
    pipe = pipe.to(device)
    image = pipe(prompt).images[0]
    image.save(output_path)
    print(f"Image saved to {output_path}")

if __name__ == "__main__":
    prompt = "A beautiful abstract vertical background, no text, 9:16 aspect ratio, vibrant colors, soft lighting"
    output_path = "assets/backgrounds/local_sd_test.png"
    generate_image(prompt, output_path)
