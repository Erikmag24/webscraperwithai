# chatbot_discussion_full.py

from gpt_api import generate_with_gpt
from ollama import generate_with_ollama
from cohere_api import generate_with_cohere
from gemini import generate_with_gemini
import os

# Mapping of available chatbot functions
CHATBOT_FUNCTIONS = {
    'gpt': generate_with_gpt,
    'ollama': generate_with_ollama,
    'cohere': generate_with_cohere,
    'gemini': generate_with_gemini
}

def load_input(query: str = None, file_path: str = None) -> str:
    """
    Load input from a query, a file, or both.
    """
    input_text = ""
    if query:
        input_text += query + "\n"
    if file_path:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            input_text += file_content
    return input_text.strip()

class ChatbotInstance:
    def __init__(self, name, type, inputs=None, additional_text=None):
        """
        Initialize a chatbot instance.

        :param name: Name of the chatbot instance.
        :param type: Type of the chatbot ('gpt', 'ollama', etc.)
        :param inputs: List of inputs (could be other chatbot instances or initial input).
        :param additional_text: Additional text to be added before generating the output.
        """
        self.name = name
        self.type = type
        self.inputs = inputs if inputs else []
        self.additional_text = additional_text
        self.output = None

    def generate_output(self):
        """
        Generate output for this chatbot instance.
        """
        # Collect inputs
        prompt_parts = []
        for inp in self.inputs:
            if isinstance(inp, ChatbotInstance):
                if inp.output is None:
                    inp.generate_output()
                prompt_parts.append(f" {inp.output}")
            else:
                prompt_parts.append(inp)

        if self.additional_text:
            prompt_parts.append(self.additional_text)

        prompt = "\n".join(prompt_parts) + f"\n{self.name}:"
        try:
            response = CHATBOT_FUNCTIONS[self.type](prompt)
            self.output = response.strip()
        except Exception as e:
            self.output = f"Error generating response. Details: {str(e)}"

def conduct_pipeline(pipeline_instances):
    """
    Conduct a pipeline of chatbot instances.

    :param pipeline_instances: List of ChatbotInstance objects.
    :return: Outputs of the final instances and the conversation history.
    """
    # Generate outputs for all instances
    conversation_history = []
    for instance in pipeline_instances:
        if instance.output is None:
            instance.generate_output()
        conversation_history.append(f"{instance.name}: {instance.output}")

    # Collect outputs from final instances (those that are not inputs to any other instance)
    final_outputs = []
    # First, get a set of all instances that are inputs to others
    input_instances = set()
    for instance in pipeline_instances:
        for inp in instance.inputs:
            if isinstance(inp, ChatbotInstance):
                input_instances.add(inp)

    # Final instances are those not in input_instances
    final_instances = [inst for inst in pipeline_instances if inst not in input_instances]

    for instance in final_instances:
        final_outputs.append((instance.name, instance.output))

    return final_outputs, conversation_history

def generate_summary(conversation_history: list, summary_bot: ChatbotInstance) -> str:
    """
    Generate a summary of the conversation using a specific chatbot.

    :param conversation_history: List of conversation interactions.
    :param summary_bot: ChatbotInstance for generating the summary.
    :return: Summary of the conversation.
    """
    prompt = "\n".join(conversation_history) + f"\n{summary_bot.name}: Please provide a summary of the above discussion."
    try:
        summary = CHATBOT_FUNCTIONS[summary_bot.type](prompt)
        return summary.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"
