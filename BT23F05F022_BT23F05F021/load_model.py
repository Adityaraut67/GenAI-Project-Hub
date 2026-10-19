from transformers import AutoModelForCausalLM
import os

model_name = "Qwen/Qwen2.5-1.5B-Instruct"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    cache_dir=os.path.join(os.getcwd(),"ai_model")
)