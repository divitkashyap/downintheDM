from dotenv import load_dotenv
from portia.cli import CLIExecutionHooks
from portia import (
    Portia,
    Config,
    ActionClarification,
    InputClarification,
    MultipleChoiceClarification,
    PlanRunState,
    StorageClass,
    LogLevel,
    LLMProvider,
    LLMModel,
    default_config,
    InMemoryToolRegistry,
    MultipleChoiceClarification,
    PortiaToolRegistry,
    PlanRunState,
    example_tool_registry,
    execution_context,
    default_config,
    DefaultToolRegistry,
)
from portia.open_source_tools.local_file_reader_tool import FileReaderTool
# from portia.open_source_tools.local_file_writer_tool import FileWriterTool
from portia.open_source_tools.search_tool import SearchTool
load_dotenv()


my_config = Config.from_default(
     storage_class=StorageClass.DISK,
    storage_dir = "demo_runs",
    default_log_level=LogLevel.DEBUG,
    llm_provider= LLMProvider.OPENAI, # You can use `MISTRAL`, `ANTHROPIC` instead
    llm_model_name=LLMModel.GPT_3_5_TURBO,
    execution_hooks=CLIExecutionHooks(),
)

my_tool_registry = InMemoryToolRegistry.from_local_tools([FileReaderTool()])



portia = Portia(
    config=my_config,
    tools=my_tool_registry + PortiaToolRegistry(config=default_config()),
    execution_hooks=CLIExecutionHooks(),
)

email = input("Enter email address: ")
name = input ("Input your name: ")

data = {"email_address": email,"name":name}
# We can also provide additional execution context to the process
with execution_context(end_user_id='end_user', additional_data=data):
    plan_run = portia.run(
        f"Read the contents of the file downintheDM/instagram_dm_text_report.txt send file contents via email ({email}) nicely formatted",
    )
# plan = portia.plan('Which stock price grew faster in 2024, Amazon or Google?')

print(plan_run.model_dump_json(indent=2))
# print(plan.model_dump_json(indent=2))