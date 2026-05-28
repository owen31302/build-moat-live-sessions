import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

def test_invoke():
    # Check if the API key is set in the environment
    # export OPENAI_API_KEY="your-api-key-here"
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please run: export OPENAI_API_KEY='your-api-key-here'")
        return

    print("Initializing ChatOpenAI model...")
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        request_timeout=20,
        max_retries=1,
    )

    messages = [
        SystemMessage(content="You are a helpful AI assistant."),
        HumanMessage(content="Hello! Can you confirm you are working by telling me a short joke?")
    ]

    print("Invoking the model... (waiting for response)")
    try:
        response = llm.invoke(messages)
        print("\n--- Model Response ---")
        print(response.content)
        print("----------------------\nSuccess! The model is working.")
    except Exception as e:
        print(f"\nAn error occurred while invoking the model:\n{e}")

if __name__ == "__main__":
    test_invoke()