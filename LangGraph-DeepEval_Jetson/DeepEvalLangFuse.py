
import asyncio, time
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import TaskCompletionMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase, MCPServer
from deepeval.metrics import MCPUseMetric
from deepeval.models import GeminiModel
from langchain_core.tools import Tool as LangChainTool, StructuredTool as LangChainStructuredTool
from mcp.types import Tool as MCPTool

#Each time this class is called, 4 requests are made to Gemini
GOOGLE_API_KEY = "YOUR_API_KEY"
Geminimodel = GeminiModel(
    model="gemini-3.1-flash-lite",
    api_key=GOOGLE_API_KEY,
    temperature=0
)

def GeminiTest():
    """Run a simple Gemini request and return model usage statistics."""
    llm_test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="Paris",
        expected_output="Paris",
    )
    answer_relevancy = AnswerRelevancyMetric(model=Geminimodel)
    try:
        score = answer_relevancy.measure(llm_test_case)
        reason = answer_relevancy.reason
        print(f"GeminiTest - Relevancy Score: {score}, Reason: {reason}")
    except Exception as e:
        print(f"Error during GeminiTest: {e}")
        score = 999
        reason = None
    return score, reason

def _langchain_tool_to_mcp_tool(tool):
    """Convert a LangChain Tool/StructuredTool into an MCP Tool definition."""
    if isinstance(tool, MCPTool):
        return tool
    #print("LangChain Tool", tool)
    name = getattr(tool, "name", None)
    if name is None and hasattr(tool, "get_name"):
        name = tool.get_name()

    description = getattr(tool, "description", "") or ""

    #input_schema = None
    #if hasattr(tool, "get_input_jsonschema"):
    #    input_schema = tool.get_input_jsonschema()
    #elif hasattr(tool, "input_schema"):
    #    input_schema = tool.input_schema
    #elif hasattr(tool, "args_schema"):
    input_schema = getattr(tool, "args_schema", None)

    if input_schema is None:
        input_schema = {"type": "object"}

    output_schema = None
    #if hasattr(tool, "get_output_jsonschema"):
    #    output_schema = tool.get_output_jsonschema()
    #elif hasattr(tool, "output_schema"):
    #    output_schema = tool.output_schema
    tempMCP=MCPTool(
        name=name,
        title=name,
        description=description,
        inputSchema=input_schema,
        outputSchema=output_schema,
    )
    #print(f"MCPTool: {tempMCP} ")
    return tempMCP


def _normalize_available_tools(tool_list):
    if tool_list is None:
        return None
    normalized = []
    for tool in tool_list:
        try:
            normalized.append(_langchain_tool_to_mcp_tool(tool))
        except Exception as e:
            print(f"Warning: failed to convert tool {getattr(tool, 'name', str(tool))}: {e}")
    return normalized


#=============================================================
# DeepEval integration
#=============================================================
class DeepEvalLangFuse(EvaluationDataset):

    def __init__(self, session_id, langfuse_client, trace_id, mcp_tools, mcp_tools_called, calc_tools_called):
        super().__init__()
        self.session_id = session_id
        self.langfuse_client = langfuse_client
        self.trace_id = trace_id
        self.traces = []
        self.mcp_tools_called = mcp_tools_called
        self.calc_tools_called = calc_tools_called
        available_tools = _normalize_available_tools(mcp_tools)
        self.mcp_server = MCPServer(    # This is the MCPServer object that deepeval's MCPUseMetric will interact with to check tool calls
            server_name="5g-core-mcp",
            transport="streamable-http",
            available_tools=available_tools,
            )
    def _extract_trace_input(self, trace):
        
        if trace.input:
            #print("Input:", trace.input)
            prompt_data = trace.input["messages"][1].get("content") or ""
            reference_output = trace.input.get("referenceOutput") or ""
            print("\033[92mInput prompt:\033[0m", prompt_data)
            print("\033[93mReference Output:\033[0m\n", reference_output)
            return prompt_data, reference_output

        return str(trace)

    def _extract_trace_output(self, trace):
        
        if trace.output:
            output=trace.output.get("messages")[-1].get("content") or ""
            print("\033[96mActual Output:\033[0m \n", output)
            return output 

        return str(trace)
    
    async def retrieve_last_trace(self):
        """Retrieve the latest Langfuse trace for the configured session."""
        max_attempts = 5
        retry_delay = 5 # seconds

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.langfuse_client.api.trace.get(trace_id=self.trace_id)
            except Exception as e:
                print(f"Attempt {attempt}/{max_attempts}: error retrieving trace: {e.body if hasattr(e, 'body') else str(e)}")
                if attempt == max_attempts:
                    return None
                await asyncio.sleep(retry_delay)
                continue

            if not response.output:
                print(f"Attempt {attempt}/{max_attempts}: no trace found yet for session {self.session_id}")
                if attempt == max_attempts:
                    return None
                await asyncio.sleep(retry_delay)
                continue
            else:
                trace = response[0] if isinstance(response, (list, tuple)) else response
                self.traces.append(trace)
                print(f"\nRetrieved last trace for session {self.session_id}, trace ID: {trace.id}")
                return trace
            
        return None

    async def load_test_cases(self):
        """Load the last trace and create a DeepEval test case from it."""
        trace = await self.retrieve_last_trace()
        if trace is None:
            return None

        prompt,refOutput = self._extract_trace_input(trace)
        output = self._extract_trace_output(trace) 
        if not output:  # Catches both None and empty strings
            print(f"No output found in trace {trace.id}. Cannot create test case.")
            return None
        test_case = LLMTestCase(
            input=prompt,
            actual_output=output,
            expected_output=refOutput,  # Use the extracted reference output
            metadata={"langfuse_session_id": self.session_id},
            tools_called=self.calc_tools_called,  
            mcp_servers=[self.mcp_server],
            mcp_tools_called=self.mcp_tools_called, # Pass the list of MCP-called tools to the test case
            context=["There are 2 users connected to the 5G core. The task is to check if the LLM can correctly use the available tools to retrieve information about all these 2 users. The LLM should be able to call the appropriate tools and return accurate information based on the input prompt."]
            #context=["There are 55 ue connected to the 5G core. The task is to check if the LLM can correctly use the available tools to retrieve information about all these 55 UEs. The LLM should be able to call the appropriate tools and return accurate information based on the input prompt."]
        )
        
        test_case._trace_dict = trace
        #print("LLM test case: ", test_case)

        return test_case

    

    async def evaluate_with_deepeval(self):
        """Retrieve the last trace and evaluate it with DeepEval."""
        test_case = await self.load_test_cases()
        if not test_case:
            return {
                "session_id": self.session_id,
                "trace_id": self.traces[-1].id if self.traces else None,
                "task_completion": [0, None],
                "mcp_use": [0, None],
                "error": "No trace or test cases available for evaluation."
            }

        task_completion_metric = TaskCompletionMetric(
            model=Geminimodel,
            include_reason=True,
            verbose_mode=True,
            async_mode=False,
        )
        mcp_use_metric = MCPUseMetric(
            model=Geminimodel,
            include_reason=True,
            verbose_mode=True,  # final score considers the min btw argument correctness and primitive usage score
            async_mode=False,
        )

        max_attempts = 5
        tc_score=999
        mcpu_score=999
        for attempt in range(1, max_attempts + 1):
            try:
                if not (tc_score>=0 and tc_score<=1):
                    tc_score = task_completion_metric.measure(test_case)
                    # Extract the reason from the metric
                    tc_reason = task_completion_metric.reason
                if not (mcpu_score>=0 and mcpu_score<=1):
                    mcpu_score = mcp_use_metric.measure(test_case) 
                    # Extract the reason from the metric
                    mcpu_reason = mcp_use_metric.reason
                break

            except Exception as e:
                print(f"Attempt {attempt}/{max_attempts}: Error occurred while evaluating with DeepEval: {e}")
                await asyncio.sleep(61)  # Wait before retrying to avoid rapid failures
                if attempt == max_attempts:
                    print("Max attempts reached. Returning partial results if available.")
                    tc_reason = None if not (tc_score>=0 and tc_score<=1) else tc_reason
                    mcpu_reason = None if not (mcpu_score>=0 and mcpu_score<=1) else mcpu_reason
                continue

        return {
            "session_id": self.session_id,
            "trace_id": self.traces[-1].id if self.traces else None,
            "task_completion": [tc_score, tc_reason],
            "mcp_use": [mcpu_score, mcpu_reason],  # Include the reason in the response
        }



