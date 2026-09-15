from typing import TypedDict, List, Dict, Any
from contextlib import asynccontextmanager
import json
import time
import traceback
import uuid

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from fastapi import FastAPI
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_ollama import ChatOllama

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from deepeval.test_case.mcp import MCPToolCall
from deepeval.test_case import ToolCall

from mcp.types import CallToolResult, TextContent

from DeepEvalLangFuse import DeepEvalLangFuse

from calculator import CALCULATOR_TOOLS

import os
LANGFUSE_SECRET_KEY="YOUR_KEY"
LANGFUSE_PUBLIC_KEY="YOUR_KEY"
LANGFUSE_BASE_URL="http://localhost:3000"
LANGFUSE_S3_BATCH_EXPORT_ENABLED="true"
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_BASE_URL"] = LANGFUSE_BASE_URL
os.environ["LANGCHAIN_TRACING_V2"] = "false" 
os.environ["LANGSMITH_TRACING"] = "false" # Disable LangSmith tracing to let deepeval work without posting on the Langsmith dashboard
os.environ["LANGFUSE_S3_BATCH_EXPORT_ENABLED"] = "true"


# Initialize Langfuse client
langfuse = get_client()
# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

def langfuse_handler(trace_id):
    """
    Langfuse callback handler that can be attached to any node to trace its execution in the dashboard.
    """
    return CallbackHandler(trace_context={"trace_id":trace_id})
# ============================================================
# GLOBAL STATE (filled at startup via lifespan)
# ============================================================
OLLAMA_BASE_URL="http://localhost:11435"
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:27b")

mcp_tools = []   # Will hold all MCP tool objects after startup
llm = None       # Will hold the bound ChatOllama instance after startup
llm_cache: Dict[str, Any] = {}
calc_called_tools: List[Any] = []

# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a 5G network AI agent.

Rules:
- Use MCP tools when needed
- Prefer tools for live/structured data
- Be concise and technical
- Do not hallucinate missing data
"""
def get_llm_for_model(model_name: str):
    """Return a cached bound ChatOllama instance for the requested model."""
    model_name = model_name or DEFAULT_OLLAMA_MODEL
    if model_name not in llm_cache:
        print(f"Creating ChatOllama instance for model: {model_name}")
        llm_cache[model_name] = ChatOllama(
            model=model_name,
            temperature=0.1,
            base_url=OLLAMA_BASE_URL,
        ).bind_tools(mcp_tools + CALCULATOR_TOOLS).with_config(
            callbacks=[token_callback]
        )
    return llm_cache[model_name]


# ============================================================
# DEBUG HELPERS
# ============================================================

def format_message(msg) -> str:
    """
    Returns a single human-readable line (or small block) describing
    a LangChain message object. Used by debug_node_input/output to
    print the conversation history in a readable way.
    """
    if isinstance(msg, SystemMessage):
        # Truncate long system prompts so they don't flood the terminal
        preview = msg.content[:200] + ("..." if len(msg.content) > 200 else "")
        return f"  [SYSTEM] {preview}"

    elif isinstance(msg, HumanMessage):
        return f"  [HUMAN]  {msg.content}"

    elif isinstance(msg, AIMessage):
        # Show text content (if any) and any tool calls the model requested
        content_preview = (
            msg.content[:200] + ("..." if len(msg.content) > 200 else "")
            if msg.content
            else "<no text content>"
        )
        tool_calls_str = ""
        if msg.tool_calls:
            calls = [f"{c['name']}({json.dumps(c['args'])})" for c in msg.tool_calls]
            tool_calls_str = f"\n           TOOL CALLS: {', '.join(calls)}"
        return f"  [AI]     {content_preview}{tool_calls_str}"

    elif isinstance(msg, ToolMessage):
        # Show the first 300 chars of the tool result
        content_preview = str(msg.content)[:300]
        if len(str(msg.content)) > 300:
            content_preview += "..."
        return f"  [TOOL]   call_id={msg.tool_call_id}\n           {content_preview}"

    else:
        # Fallback for any unexpected message types
        return f"  [{type(msg).__name__.upper()}] {str(msg)[:200]}"


def debug_node_input(node_name: str, state: "GraphState"):
    """
    Prints the full message history and current token counters
    that are being passed INTO a node. Useful for verifying that
    each node receives exactly the context you expect.
    """
    print(f"\n{'='*60}")
    print(f">>> NODE INPUT: {node_name}")
    print(f"{'='*60}")
    print(f"  Messages ({len(state['messages'])} total):")
    for i, msg in enumerate(state["messages"]):
        print(f"  [{i}] {format_message(msg)}")
    print(f"  Token usage (this iteration): {state.get('token_usage', {})}")
    print(f"{'='*60}")


def debug_node_output(node_name: str, output: dict):
    """
    Prints only the LAST (newly added) message from a node's output,
    along with the updated token counters. Avoids repeating the full
    history that was already printed in debug_node_input.
    """
    print(f"\n{'='*60}")
    print(f"<<< NODE OUTPUT: {node_name}")
    print(f"{'='*60}")
    new_messages = output.get("messages", [])
    if new_messages:
        print(f"  New message added:")
        print(f"  {format_message(new_messages[-1])}")
    print(f"  Token usage (this iteration): {output.get('token_usage', {})}")
    print(f"{'='*60}\n")


# ============================================================
# TOKEN TRACKER
# ============================================================

class TokenUsageCallback(BaseCallbackHandler):
    """
    LangChain callback that intercepts on_llm_end events to extract
    token counts from Ollama's generation_info dict.

    NOTE: Ollama does NOT populate llm_output (which is always None).
    Token counts live in response.generations[0][0].generation_info
    under the keys 'prompt_eval_count' and 'eval_count'.

    This object is reset to zero before every LLM call (see llm_node)
    so that each iteration's usage is measured independently.
    The webhook accumulates the per-iteration totals into a grand total.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Zero out all counters. Called before each LLM invocation."""
        self.usage = {
            "promptTokens": 0,
            "completionTokens": 0,
            "totalTokens": 0,
        }

    def on_llm_end(self, response, **kwargs):
        try:
            #print(response)
            gen_info = response.generations[0][0].generation_info or {}
            #print(gen_info)
            prompt_tokens = gen_info.get("prompt_eval_count", 0)
            completion_tokens = gen_info.get("eval_count", 0)

            self.usage["promptTokens"] += prompt_tokens
            self.usage["completionTokens"] += completion_tokens
            self.usage["totalTokens"] += prompt_tokens + completion_tokens

        except (IndexError, AttributeError):
            # If Ollama returns an unexpected structure, skip silently
            pass


# Single global callback instance — reset before each LLM call
token_callback = TokenUsageCallback()


# ============================================================
# GRAPH STATE
# ============================================================

class GraphState(TypedDict):
    """
    The state object that flows through every node in the LangGraph.

    - messages:      Full conversation history (system, human, AI, tool messages)
    - token_usage:   Token counts for the CURRENT LLM iteration only (reset each time)
    - total_usage:   Accumulated token counts across ALL iterations in this request
    - ollama_model:  The Ollama model to use for this request
    - model_usage_history: Per-LLM iteration usage statistics
    """
    messages: List
    token_usage: Dict[str, int]   # Per-iteration usage (reset each LLM call)
    total_usage: Dict[str, int]   # Grand total for the full request
    ollama_model: str
    model_usage_history: List[Dict[str, Any]]


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup and once at shutdown.
    Initialises the MCP client (loads available tools) and the LLM,
    then yields control to FastAPI. Everything after yield is cleanup.
    """
    global mcp_client, llm, mcp_tools

    # -- MCP CLIENT -------------------------------------------------
    # MultiServerMCPClient connects to one or more MCP servers and
    # exposes their tools as standard LangChain tool objects.
    mcp_client = MultiServerMCPClient(
        {
            "5g-core-mcp": {
                "transport": "http",
                "url": "http://100.80.53.32:8086/mcp",
            }
        }
    )

    # get_tools() must be awaited — it fetches the tool manifest from the server
    try:
        async with mcp_client.session("5g-core-mcp") as session:
                mcp_tools = await load_mcp_tools(session)
         #mcp_tools = await mcp_client.get_tools()
        print("✅ MCP tools loaded:", [t.name for t in mcp_tools])
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}") 
        
    from DeepEvalLangFuse import GeminiTest
    print("GoogleLLMTest - score and reason:", GeminiTest())
    # -- LLM --------------------------------------------------------
    # bind_tools() tells the model which tools it can call.
    # with_config(callbacks=...) attaches the token tracker so
    # on_llm_end fires after every completion.
    llm = get_llm_for_model(DEFAULT_OLLAMA_MODEL)

    yield  # FastAPI serves requests between here and shutdown

    print("Shutting down...")


app = FastAPI(lifespan=lifespan)


# ============================================================
# LANGGRAPH NODES
# ============================================================
#@observe() # Langfuse decorator to trace this node's execution in the dashboard
def llm_node(state: GraphState):
    """
    Core reasoning node. Sends the full message history to the LLM
    and appends the AI response to state.

    Token tracking:
      1. Reset the callback counters to zero (isolates this iteration).
      2. Invoke the LLM (on_llm_end fires inside, populating token_callback.usage).
      3. Snapshot the per-iteration usage into state['token_usage'].
      4. Add the snapshot to the running state['total_usage'] grand total.
    """
    debug_node_input("LLM", state)

    # Step 1 — Reset so this iteration's tokens are measured in isolation
    token_callback.reset()

    # Step 2 — Call the model with the current conversation history
    model_name = state.get("ollama_model", DEFAULT_OLLAMA_MODEL)
    response = get_llm_for_model(model_name).invoke(state["messages"])

    # Step 3 — Snapshot per-iteration usage (shallow copy to freeze the values)
    iteration_usage = token_callback.usage.copy()

    # Step 4 — Accumulate into the grand total that persists across iterations
    prev_total = state.get("total_usage", {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0})
    new_total = {
        "promptTokens":     prev_total["promptTokens"]     + iteration_usage["promptTokens"],
        "completionTokens": prev_total["completionTokens"] + iteration_usage["completionTokens"],
        "totalTokens":      prev_total["totalTokens"]      + iteration_usage["totalTokens"],
    }

    print(f"\n  💰 Iteration tokens : {iteration_usage}")
    print(f"  💰 Running total    : {new_total}")

    model_usage = {
        "model": model_name,
        "promptTokens": iteration_usage["promptTokens"],
        "completionTokens": iteration_usage["completionTokens"],
        "totalTokens": iteration_usage["totalTokens"],
    }
    output = {
        "messages":    state["messages"] + [response],
        "token_usage": iteration_usage,   # Only this iteration
        "total_usage": new_total,         # Accumulated across all iterations
        "model_usage_history": state.get("model_usage_history", []) + [model_usage],
    }

    debug_node_output("LLM", output)
    return output


def tool_router(state: GraphState):
    """
    Conditional edge function — decides the next node after llm_node.
    If the last AI message contains tool_calls, route to tool_node.
    Otherwise the conversation is complete, route to END.
    """
    last = state["messages"][-1]
    decision = "tools" if getattr(last, "tool_calls", None) else END

    print(f"\n--- ROUTER: {'→ tool_node' if decision == 'tools' else '→ END'} ---")
    if decision == "tools":
        # List the tools about to be called for easy debugging
        calls = [c["name"] for c in last.tool_calls]
        print(f"    Tool calls queued: {calls}")

    return decision

#@observe()
async def tool_node(state: GraphState):
    """
    Executes every tool call requested by the last AI message in parallel
    (sequentially here, but can be parallelised with asyncio.gather).

    Handles both MCP tools and calculator tools.
    Each tool result is wrapped in a ToolMessage so the LLM can read it
    on the next iteration. Token usage is not affected here (no LLM call).
    """
    debug_node_input("TOOL", state)

    last = state["messages"][-1]
    results = []

    try:
        async with mcp_client.session("5g-core-mcp") as session:
            mcp_tools = await load_mcp_tools(session)  # Ensure we have the latest tools from the MCP server
            all_tools = mcp_tools + CALCULATOR_TOOLS

            for call in last.tool_calls:
                print(f"\n  ⚙️  Calling tool : {call['name']}")
                print(f"      Args         : {json.dumps(call['args'], indent=6)}")

                # Look up the matching tool object by name
                tool = next((t for t in all_tools if t.name == call["name"]), None)

                if tool is None:
                    error_msg = f"Tool '{call['name']}' not found"
                    print(f"      ❌ Error: {error_msg}")
                    results.append(
                        ToolMessage(
                            content=error_msg,
                            tool_call_id=call["id"],
                        )
                    )
                    continue

                # Check if it's a calculator tool (local) or MCP tool (remote)
                is_calculator_tool = tool in CALCULATOR_TOOLS

                try:
                    if is_calculator_tool:
                        # Calculator tools use regular invoke
                        output = await tool.ainvoke(call["args"]) if hasattr(tool, 'ainvoke') else tool.invoke(call["args"])
                    else:
                        # MCP tools use ainvoke to communicate with the server
                        output = await tool.ainvoke(call["args"])

                    # Convert output to CallToolResult for DeepEval evaluation
                    output = CallToolResult(
                        content=[TextContent(type="text", text=str(output))],
                        isError=False
                    )
                except Exception as e:
                    # Handle errors from tool execution
                    error_msg = f"Error executing {call['name']}: {str(e)}"
                    print(f"      ❌ {error_msg}")
                    output = CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True
                    )

                # Store this tool call as a DeepEval MCPToolCall object
                if is_calculator_tool:
                    calc_called_tools.append(
                        ToolCall(
                            name=call["name"],
                            input_parameters=call["args"],
                            output=output,
                        )
                    )
                else:
                    mcp_called_tools.append(
                        MCPToolCall(
                            name=call["name"],
                            args=call["args"],
                            result=output,
                        )
                    )

                result_preview = str(output)[:300] + ("..." if len(str(output)) > 300 else "")
                print(f"      Result preview: {result_preview}")

                # Wrap the raw output in a ToolMessage linked to the original call ID
                results.append(
                    ToolMessage(
                        content=str(output),
                        tool_call_id=call["id"],
                    )
                )
    except Exception as e:
        print(f"Error retrieving or executing MCP tools: {e}")
        print(traceback.format_exc())
        # Add a failure ToolMessage for each requested tool if we cannot establish a session
        for call in last.tool_calls:
            results.append(
                ToolMessage(
                    content=f"MCP tool execution failed: {e}",
                    tool_call_id=call["id"],
                )
            )

    result_state = {
        "messages":    state["messages"] + results,
        "token_usage": state["token_usage"],  # Unchanged — no LLM call here
        "total_usage": state["total_usage"],  # Unchanged — no LLM call here
        "model_usage_history": state.get("model_usage_history", []),
    }

    debug_node_output("TOOL", result_state)
    return result_state


# ============================================================
# BUILD GRAPH
# ============================================================

# Create the graph with our typed state schema
graph = StateGraph(GraphState)

# Register nodes
graph.add_node("llm",   llm_node)
graph.add_node("tools", tool_node)

# llm_node is always the entry point
graph.set_entry_point("llm")

# After llm_node: either call tools or finish
graph.add_conditional_edges(
    "llm",
    tool_router,
    {
        "tools": "tools",
        END:     END,
    },
)

# After tool_node: always go back to llm_node for the next reasoning step
graph.add_edge("tools", "llm")

# MemorySaver persists state between requests using thread_id as the key
memory = MemorySaver()
app_graph = graph.compile(checkpointer=memory)

# from IPython.display import Image, display
# Show the agent
# display(Image(app_graph.get_graph(xray=True).draw_mermaid_png()))

# ============================================================
# BACKGROUND EVALUATION
# ============================================================

async def run_evaluation(session_id: str, langfuse_client, trace_id: str):
    """
    Runs the DeepEval evaluation.
    """
     # Variable to store all the tools called during the conversation, to be used in the evaluation
    print("="*60)
    print(f"\nStarting DeepEval evaluation for session {session_id} with trace ID {trace_id}...\n")
    d = DeepEvalLangFuse(session_id, langfuse_client, trace_id, mcp_tools, mcp_called_tools, calc_called_tools)
    #gemini_usage = d.get_gemini_model_usage()
    #print(f"Gemini model usage before evaluation: {gemini_usage}")
    eval_result = await d.evaluate_with_deepeval()
    #
    # 
    # 
    # eval_result["gemini_usage"] = gemini_usage
    print(f"\033[95mDeepEval\033[0m result: {eval_result}")
    #score = eval_result["task_completion_score"]
    #reason = eval_result["task_completion_reason"]
    #push result to langfuse as trace metadata
    try:
        langfuse_client.create_score(
            trace_id=trace_id,
            name="Task Completion Score",
            value=eval_result["task_completion"][0],
            comment=eval_result["task_completion"][1]
        )
        print(f"\nTask Completion Score pushed to Langfuse for trace {trace_id}")
        langfuse_client.create_score(
            trace_id=trace_id,
            name="MCP Use Score",
            value=eval_result["mcp_use"][0] or 0,
            comment=eval_result["mcp_use"][1]
        )
        print(f"\nMCP Use Score pushed to Langfuse for trace {trace_id}")
        print("="*60)
    except Exception as e:
        print(f"Error creating score in Langfuse: {e}")
    return eval_result
    # Optionally, you can store the score somewhere or send it to another endpoint

# ============================================================
# API INPUT MODEL
# ============================================================

class ChatInput(BaseModel):
    """Expected JSON body for POST requests to the webhook endpoint."""
    chatInput: str   # The user's message
    sessionId: str   # Used as thread_id to resume conversation memory
    referenceOutput: str  # For correctness evaluation
    ollamaModel: str = None  # Optional model selection for Ollama


# ============================================================
# WEBHOOK
# ============================================================

@app.post("/langGraph-webhook")
async def chat(payload: ChatInput):
    """
    Entry point for all chat requests.

    Builds the initial state (system prompt + user message),
    runs the full LangGraph until END, then returns the final
    AI response and the grand total token usage across all
    LLM iterations that happened during this request.
    The evaluation is started in the background after sending the response.
    """
    global mcp_called_tools, calc_called_tools
    mcp_called_tools = []  # Reset the MCP-called tools for each new request
    calc_called_tools = []  # Reset the calculator-only called tools for each new request
    print(f"\n{'#'*60}")
    is_cogito = False  # Reset the Cogito flag for each new request
    requested_model = payload.ollamaModel or DEFAULT_OLLAMA_MODEL
    if requested_model in ["cogito:3b", "cogito:8b", "cogito:32b"]:
        is_cogito = True
    print(f"# NEW REQUEST  — session : {payload.sessionId}")
    print(f"# User input             : {payload.chatInput}")
    print(f"# Ollama model           : {requested_model}")

    
    
    trace_id = uuid.uuid4().hex  # langfuse trace id must be 32 lowercase hex chars
    print(f"Generated trace ID for Langfuse: {trace_id}")
    print(f"{'#'*60}")
    start_time = time.perf_counter()
    result = await app_graph.ainvoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT if not is_cogito else SYSTEM_PROMPT + "\n\nEnable deep thinking subroutine."),
                HumanMessage(content=payload.chatInput),
            ],
            "ollama_model": requested_model,
            "referenceOutput": payload.referenceOutput,
            "model_usage_history": [],
            # Both counters start at zero at the beginning of each request
            "token_usage": {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0},
            "total_usage": {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0},
        },
        config={
            "configurable": {
                "thread_id": payload.sessionId,
                "run_name": "5g-agent",
            },
            "callbacks": [langfuse_handler(trace_id)],
        },
    )

    
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    print(f"# LATENCY               : {latency_ms:.2f} ms")
    final_answer  = result["messages"][-1].content
    # print(result)
    # total_usage is the sum of every LLM iteration in this request
    grand_total   = result["total_usage"]

    print(f"\n{'#'*60}")
    print(f"# FINAL ANSWER  : {final_answer[:500]}{'...' if len(final_answer) > 500 else ''}")
    print(f"# TOTAL TOKENS  : {grand_total}")
    print(f"{'#'*60}\n")

    # Start evaluation in background
    #background_tasks = BackgroundTasks()
    #background_tasks.add_task(run_evaluation, payload.sessionId, langfuse)
    evaluation_result = await run_evaluation(payload.sessionId, langfuse, trace_id)

    
    return {
        "evaluationResult":   evaluation_result,
        "sessionId":          payload.sessionId,
        "traceId":            trace_id,
        "finalAnswer":        final_answer,
        "all_trace_messages": [format_message(m) for m in result["messages"]],
        "tokenUsageEstimate": grand_total,   # Total for the whole request, not just last iteration
        "modelUsageStatistics": result.get("model_usage_history", []),
        "latencyMs":          latency_ms,
    }
