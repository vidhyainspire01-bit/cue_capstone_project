from openai import OpenAI
from common.config import LLM_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary(context_chunks):
    joined_text = "\n\n".join(context_chunks)
    prompt = f"""You are an AI analyst generating a concise, citable summary.
    Based on the following evidence, provide:
    - Top Risks
    - Open Commitments
    - Recent Escalations
    - Highlights
    Include inline citation markers like [source_path].
    Evidence:
    {joined_text}
    """
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()
