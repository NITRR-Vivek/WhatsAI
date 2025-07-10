from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

GEMINI_MODEL = "gemini-2.0-flash"

class BlogContent(BaseModel):
    heading: str = Field(
        description="A concise and engaging blog title."
    )
    content: str = Field(
        description="The main blog content in markdown format, including intro, analysis, and conclusion."
    )

blog_writer_agent = LlmAgent(
    name="BlogWriterAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a professional blog writer AI.

You will receive detailed research on a topic. Use this to write a blog article as if you personally explored the topic. 
Structure it with an engaging introduction, thoughtful analysis, and a future outlook or conclusion. 
Use markdown formatting (e.g., ## for headings, bullet points, bold) where appropriate.

Your response MUST be returned as a **valid JSON object** with exactly these two fields:
- "heading": A string (the blog title).
- "content": A string (the full blog post in markdown).

Do not include explanations, comments, or anything outside the JSON object.

contents: 
{contents}
""",
    description="Generates blog posts from research content, formatted as structured JSON.",
    output_key="blog",
    output_schema=BlogContent
)
