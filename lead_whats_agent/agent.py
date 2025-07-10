from google.adk.agents import SequentialAgent
from .subagents.trendFinder import trend_finder_agent
from .subagents.contentFinder import content_finder_agent
from .subagents.blogWriter import blog_writer_agent

root_agent = SequentialAgent(
    name="ExperinceWritingPipeline",
    sub_agents=[trend_finder_agent, content_finder_agent,blog_writer_agent],
    description="A pipeline that find the current top web search trend, research about particular topic and then write blog of experience and analysis about that topic.",
)
