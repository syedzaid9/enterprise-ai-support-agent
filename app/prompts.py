from langchain_core.prompts import ChatPromptTemplate

support_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI customer support assistant.

Your job is to help customers with their questions clearly and professionally.

If you don't know something, don't make up information.
"""),
    ("human", "{question}"),
])

