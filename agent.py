import os
import io
import contextlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")       # render charts to file, no popup window
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from anthropic import Anthropic

# --Setup--
load_dotenv()
client=Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
df=pd.read_csv("data/health_canada.csv")

# The agent's "tool": run the python code we give it.
TOOLS=[
    {
        "name": "run_python",
        "description": (
            "Run python code to analyze the dataframe `df`"
            " and answer the user's question."
            "The code has access to `df`(pandas), `pd`, and `plt (matplotlip)`."
            " To return a chart, save it with plt.savefig('chart.png'). Use orint()"
            "to surface any numeric result. "
        ),
        "input_schema":{
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Valid Python using df, pd, and plt.",
                }
            },
            "required": ["code"],
        },
    }
]

# --The function that actually runs Claude's code--
def run_python(code:str) -> str:
    """ Execute Claude's code, capturing printed output. 
    Returns output or error."""
    buffer=io.StringIO()
    scope={"df":df,"pd":pd,"plt":plt}
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code,scope) # runs the LLM-written code
        return buffer.getvalue() or "(code ran, no printed output)"
    except Exception as e:
        return f"Error:{type(e).__name__}:{e}" # fed back to claude to fix
    
## --The agent loop--
def ask(question:str, max_turns: int=5) -> str:
    # Give claude the REAL columns so that it can't invent fake ones.
    system=(
        "You are data analyst working with a pandas dataframe `df`."
        f"Its columns are: {list(df.columns)}."
        "When asked a question, call run_python with code that answers it."
        "If a chart helps, save it to chart.png. After the tool result," \
        "give a consice plain-English interpretation of what data shows."
        "Only use columns that actually exist."
    )
    messages=[{"role":"user","content":question}]
    for _ in range(max_turns): # The retry / multi-step loop
        response= client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=system,
            tools=TOOLS,
            messages=messages
        )
        #Keep Claude's turn in conversation.
        messages.append({"role":"assistant","content":response.content})
        if response.stop_reason != "tool_use":
            # No tool call -> Claude gave its final text answer.
            return "".join(b.text for b in response.content if b.type =="text")
        # Find the tool call, run it, send the result back.
        tool_results=[]
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n[Claude ran code]: \n {block.input['code']}\n")
                result=run_python(block.input["code"])
                print(f"[Result]:{result}\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content":result,
                })
        messages.append({"role":"user","content":tool_results})
    return "Stopped: hit the max number of turns without a final answer."

# --Try it--
if __name__=="__main__":
    answer=ask("Which province has the highest value, and " \
    "show it as a bar chart?")
    print("\n=== INTERPRETATION ===")
    print(answer)