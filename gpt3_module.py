import openai


# Замените "your_api_key" на ваш API ключ от OpenAI
openai.api_key = "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"

def generate_text(prompt, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3500,
        n=1,
        temperature=0.5,
    )
    return response.choices[0].message["content"].strip()