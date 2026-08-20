
from watsonx_client import get_model

model = get_model(max_tokens=50)
response = model.generate_text(prompt="In one sentence, what is a Gantt chart?")

print("watsonx responded:")
print(response)
