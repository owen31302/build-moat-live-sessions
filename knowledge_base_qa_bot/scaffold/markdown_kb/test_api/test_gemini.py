import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

def test_invoke():
    # Check if the Google API key is set
    # export GOOGLE_API_KEY="your-new-gemini-key"
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        print("Please run: export GOOGLE_API_KEY='your-gemini-api-key-here'")
        return

    print("Initializing Gemini model...")
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        timeout=20,
        max_retries=0,
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
        print("----------------------\nSuccess! The Gemini model is working.")
    except Exception as e:
        print(f"\nAn error occurred while invoking the model:\n{e}")

if __name__ == "__main__":
    test_invoke()