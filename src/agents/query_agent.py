from settings import ORGANIZATION_NAME
def create_query_agent(
    model="gemini-2.0-flash",
    temperature=0.1,
    api_key=None,
    prompt_path="src/utils/prompts.yml"
):
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import create_openai_functions_agent, AgentExecutor
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from src.tools.query_tool import get_context
    from src.utils.yaml_loader import load_prompts

    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
    )
    tools = [get_context]
    prompts = load_prompts(prompt_path)
    prompt_text = prompts["query_agent_prompt"].format(organization_name = ORGANIZATION_NAME)
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
