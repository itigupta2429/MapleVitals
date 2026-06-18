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
CONTRACT = open("data/statcan_contract.yaml").read()   # the data-quality rules, as plain text


# The agent's "tool": run the python code we give it.
TOOLS=[
    {
        "name": "run_python",
        "description": (
            "Run python code to analyze the dataframe `df`"
            " and answer the user's question."
            "The code has access to `df`(pandas), `pd`, and `plt (matplotlib)`."
            "To return a chart, save it with plt.savefig(<filename>) using the exact"
            " filename the user specifies in their question. Use print()"
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
def ask(question:str, max_turns: int=20) -> str:
    # Give claude the REAL columns so that it can't invent fake ones.
    system=(
        "You are data analyst working with a pandas dataframe `df`."
        f"Its columns are: {list(df.columns)}."
        "When asked a question, call run_python with code that answers it."
        "If a chart helps, save it to the exact .png filename given in the user's "
        "question (e.g. plt.savefig('mental_health_alberta.png')). After the tool result,"
        "give a consice plain-English interpretation of what data shows."
        "Only use columns that actually exist.\n\n"
        "=== DATA-QUALITY CONTRACT — apply before every final answer ===\n"
        f"{CONTRACT}\n"
        "=== HOW TO USE THE CONTRACT ===\n"
        "Before giving your final interpretation, check EVERY figure you report "
        "against the contract above:\n"
        "0. When you filter df to answer a question, ALWAYS include the STATUS "
        "column in what you inspect — do not select only the VALUE. You cannot "
        "report a flag you never read.\n"
        "1. Read the STATUS column for each figure and apply the matching flag's "
        "action. For an E flag, state in plain language that the estimate has high "
        "variability and should be used with caution — describing the confidence "
        "interval does NOT satisfy this.\n"
        "2. The -1/0/1 'Statistically different' rows are significance CODES, not "
        "numbers — translate them to words, never report the raw number.\n"
        "3. The two health indicators do NOT sum to 100%; never infer one by "
        "subtracting the other.\n"
        "4. GOLDEN RULE: if you hit any flag or symbol NOT in the contract, treat "
        "it as a quality concern — surface it, don't assume it's safe.\n"
        "5. For every figure, state which quality flag applies and what you did "
        "about it. If a figure is F or suppressed (x), do not present it as a "
        "usable number.\n")
    
    messages=[{"role":"user","content":question}]
    for _ in range(max_turns): # The retry / multi-step loop
        response= client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8000,
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
if __name__ == "__main__":
    os.makedirs("examples", exist_ok=True)

    runs = {
        "mental_health_alberta_18_34.png": '''In Alberta, how has the share reporting FAIR or POOR mental health changed from 2015 to 2024 for the 18-to-34 age group? Plot one line chart with two lines (males = blue circles, females = red squares) — no other age groups, no province faceting. Drop "Total, 18 and over". Use percentage values only (ignore -1/0/1 significance codes); draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Young Albertans reporting fair or poor mental health, 2015–2024 (by gender)". Then give me the single clearest pattern, based on the numbers you computed.''',

        "heavy_drinking_alberta_2024.png": '''For Alberta in 2024, compare the share reporting HEAVY DRINKING across the four age groups (18-34, 35-49, 50-64, 65+), males and females in one chart. Use a grouped horizontal bar chart, drop "Total, 18 and over", label each bar with its value, outline any E-flagged bar and exclude it from the high/low claim. Title it exactly: "Which Albertans drink the heaviest? Heavy drinking by age and gender, 2024". One sentence: which age group drinks heaviest and how the genders differ.''',

        "smoking_trend_18_34.png": '''Plot the trend in CURRENT SMOKING (daily or occasional) for Canada-level adults aged 18-to-34, 2015 to 2024, as two lines (males and females). Drop "Total, 18 and over". Use percentage values only; draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Are young Canadians smoking less? Current smoking, ages 18–34, 2015–2024". In one sentence, quantify the overall direction and the approximate total change in percentage points across the period.''',

        "Self-reported_obesity__ranked_by_province__2024.png": '''Across all provinces in 2024, rank the share of adults aged 18-34 who are OBESE (self-reported BMI), highest to lowest, for young women and young men separately. Produce two side-by-side horizontal bar panels: left = young women, right = young men, each sorted high to low and labelled with its value. Show E-flagged provinces as hatched/outlined bars and exclude them from any "highest/lowest" statement. Title the left panel exactly "Self-reported obesity in young women, ranked by province, 2024" and the right panel exactly "Self-reported obesity in young men, ranked by province, 2024". One sentence per panel on the ranking and the gap between top and bottom (non-flagged).''',

        "access_vs_health_alberta.png": '''For Alberta women aged 18-34, plot two indicators on one chart over 2015-2024: share WITH a regular healthcare provider and share reporting VERY GOOD or EXCELLENT perceived health. Two lines, clearly labelled, percentage values only (ignore -1/0/1 significance codes). Do NOT assume the two indicators are related or sum to anything. Draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Regular provider vs. perceived health: young Alberta women, 2015–2024". In one sentence, say whether the two indicators moved together or diverged over the period, based on the values.''',
    }

    with open("examples/interpretation.txt", "w", encoding="utf-8") as f:
        for fname, prompt in runs.items():
            full = prompt + f'\nSave the figure as "examples/{fname}" (use that exact filename in plt.savefig).'
            print(f"\n{'='*70}\nRunning: {fname}\n{'='*70}")
            answer = ask(full)
            f.write(f"\n\n{'='*70}\n{fname}\n{'='*70}\n{answer}\n")
            f.flush()
            print(answer)
            print(f"✓ saved examples/{fname}")

    print("\nAll done. Charts in examples/, interpretations in examples/interpretation.txt")