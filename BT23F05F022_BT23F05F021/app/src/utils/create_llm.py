from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from dotenv import load_dotenv
import os

load_dotenv()

model_name = os.getenv("MODEL","Qwen/Qwen2.5-0.5B-Instruct")

tokenizer = AutoTokenizer.from_pretrained(model_name,cache_dir=os.path.join(os.getcwd(),"ai_model"))

def create_llm():

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=os.path.join(os.getcwd(),"ai_model")
        )

    pipe = pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        return_full_text=False,
        do_sample=False
        )
    
    llm = HuggingFacePipeline(
        pipeline=pipe
        )
    
    return llm