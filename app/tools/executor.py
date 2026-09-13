from app import prompts
from langchain_core.messages import ToolMessage

def execute_tools(response,tools_by_name):
    """
    Execute all tools requested by the model and return the resulting ToolMessage.
    """
    tool_messages = []
    for tool_call in response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool = tools_by_name.get(tool_name)
        tool_result = tool.invoke(tool_args)
        print(f'\nExecuteing Tool: {tool_name}')
        print("Arguments:",tool_args)
        print("Result:",tool_result)

        # create ToolMessage
        tool_message = ToolMessage(
            content = str(tool_result),
            tool_call_id = tool_call['id']
        )

        tool_messages.append(tool_message)

    return tool_messages

        
        
        