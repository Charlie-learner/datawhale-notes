import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()

required_variables = [
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "MODEL_NAME",
]
missing_variables = [
    name for name in required_variables if not os.environ.get(name)
]

if missing_variables:
    raise RuntimeError("缺少环境变量：" + ", ".join(missing_variables))


model = ChatOpenAI(
    model=os.environ["MODEL_NAME"],
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)


def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: Name of the city to query.
    """
    print(f"[工具被调用] get_weather(city={city!r})")
    return f"{city}今天晴朗，气温 24 摄氏度。"


agent = create_deep_agent(
    model=model,
    tools=[get_weather],
    system_prompt=(
        "你是一位天气助手。"
        "回答天气问题时必须调用 get_weather 工具，"
        "不要凭空编造工具没有返回的信息。"
    ),
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "北京今天天气怎么样？请调用天气工具后回答。",
            }
        ]
    }
)

print("\n最终回答：")
print(result["messages"][-1].content)
