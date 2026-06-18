import os
import io
import sys
import json
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
# CHANGE 1: scope is passed IN, not rebuilt every call. Variables now persist
# across tool calls within one question -> no more NameError thrashing (= fewer
# turns = less money). `ask` creates a fresh scope per question so nothing leaks
# between the five questions.
def run_python(code:str, scope:dict) -> str:
    """ Execute Claude's code in the given persistent scope, capturing printed
    output. Returns output or error."""
    buffer=io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code,scope) # runs the LLM-written code
        return buffer.getvalue() or "(code ran, no printed output)"
    except Exception as e:
        return f"Error:{type(e).__name__}:{e}" # fed back to claude to fix
    
## --The agent loop--
def ask(question:str, max_turns: int=20) -> str:
    # CHANGE 1: one scope per question. Persists across this question's tool
    # calls, but is fresh for each new question so variables don't leak.
    scope = {"df": df, "pd": pd, "plt": plt}
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
        "usable number.\n\n"
        "=== CORRECTNESS — as important as the quality contract above ===\n"
        "The contract catches FLAG errors. It does NOT catch WRONG NUMBERS. You "
        "have no eyes — you CANNOT see the chart you saved — so:\n"
        "A. Every figure, percentage, ranking, 'highest', or 'lowest' in your final "
        "answer MUST come from text you actually printed with run_python and read "
        "back. Never state a number you did not print.\n"
        "B. Before ANY 'highest/lowest' or ranking claim, first print the FULL "
        "sorted table (value + STATUS), then read the top/bottom row from that "
        "printed output. Do not eyeball, estimate, or recall from memory.\n"
        "C. Describe only what the printed numbers say — never what the chart "
        "'shows' or 'looks like'. You cannot see it.\n\n"
        "=== OUTPUT FORMAT — your answer is shown directly to end users in a web app ===\n"
        "Output clean Markdown only. Do NOT include: filler like 'Perfect!' or "
        "'Now let me...'; ANY file path or .png filename; any mention of saving a "
        "figure. Start directly with the interpretation (a heading or a sentence).\n")
    
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
                result=run_python(block.input["code"], scope)
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
    OUT = "examples/interpretations.json"   # CHANGE 4: Streamlit reads this

    # slug -> {label shown in the Streamlit dropdown, chart path, prompt}
    QUESTIONS = {
        "mental_health_alberta_18_34": {
            "label": "How does fair/poor mental health vary by age & gender in Alberta (18–34)?",
            "chart": "examples/mental_health_alberta_18_34.png",
            "prompt": '''In Alberta, how has the share reporting FAIR or POOR mental health changed from 2015 to 2024 for the 18-to-34 age group? Plot one line chart with two lines (males = blue circles, females = red squares) — no other age groups, no province faceting. Drop "Total, 18 and over". Use percentage values only (ignore -1/0/1 significance codes); draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Young Albertans reporting fair or poor mental health, 2015–2024 (by gender)". Then give me the single clearest pattern, based on the numbers you computed.''',
        },
        "heavy_drinking_alberta_2024": {
            "label": "What does heavy drinking look like in Alberta (2024)?",
            "chart": "examples/heavy_drinking_alberta_2024.png",
            "prompt": '''For Alberta in 2024, compare the share reporting HEAVY DRINKING across the four age groups (18-34, 35-49, 50-64, 65+), males and females in one chart. Use a grouped horizontal bar chart, drop "Total, 18 and over", label each bar with its value, outline any E-flagged bar and exclude it from the high/low claim. Title it exactly: "Which Albertans drink the heaviest? Heavy drinking by age and gender, 2024". One sentence: which age group drinks heaviest and how the genders differ.''',
        },
        "smoking_trend_18_34": {
            "label": "Are young Canadians smoking less (18–34)?",
            "chart": "examples/smoking_trend_18_34.png",
            "prompt": '''Plot the trend in CURRENT SMOKING (daily or occasional) for Canada-level adults aged 18-to-34, 2015 to 2024, as two lines (males and females). Drop "Total, 18 and over". Use percentage values only; draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Are young Canadians smoking less? Current smoking, ages 18–34, 2015–2024". In one sentence, quantify the overall direction and the approximate total change in percentage points across the period.''',
        },
        "obesity_by_province_2024": {
            "label": "How does self-reported obesity vary by province (2024)?",
            "chart": "examples/Self-reported_obesity__ranked_by_province__2024.png",
            "prompt": '''Across all provinces in 2024, rank the share of adults aged 18-34 who are OBESE (self-reported BMI), highest to lowest, for young women and young men separately. Produce two side-by-side horizontal bar panels: left = young women, right = young men, each sorted high to low and labelled with its value. Show E-flagged provinces as hatched/outlined bars and exclude them from any "highest/lowest" statement. Title the left panel exactly "Self-reported obesity in young women, ranked by province, 2024" and the right panel exactly "Self-reported obesity in young men, ranked by province, 2024". One sentence per panel on the ranking and the gap between top and bottom (non-flagged).''',
        },
        "access_vs_health_alberta": {
            "label": "Healthcare access vs. perceived health: young Alberta women",
            "chart": "examples/access_vs_health_alberta.png",
            "prompt": '''For Alberta women aged 18-34, plot two indicators on one chart over 2015-2024: share WITH a regular healthcare provider and share reporting VERY GOOD or EXCELLENT perceived health. Two lines, clearly labelled, percentage values only (ignore -1/0/1 significance codes). Do NOT assume the two indicators are related or sum to anything. Draw E-flagged points as hollow markers on a dashed segment. Title it exactly: "Regular provider vs. perceived health: young Alberta women, 2015–2024". In one sentence, say whether the two indicators moved together or diverged over the period, based on the values.''',
        },
    }

    def load_results():
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as f:
                return json.load(f)
        return {}

    # MONEY SAVER: pass slug(s) on the command line to run ONLY those.
    #   python agent.py obesity_by_province_2024     # re-runs just the broken one
    # With no args, runs all five.
    to_run = [s for s in sys.argv[1:] if s in QUESTIONS] or list(QUESTIONS)

    results = load_results()   # keep whatever is already saved
    for slug in to_run:
        q = QUESTIONS[slug]
        full = q["prompt"] + f'\nSave the figure as "{q["chart"]}" (use that exact filename in plt.savefig).'
        print(f"\n{'='*70}\nRunning: {slug}\n{'='*70}")
        answer = ask(full)
        # merge-save after EACH question: the other entries survive, and if a
        # later question crashes you don't lose the ones already done.
        results[slug] = {"label": q["label"], "chart": q["chart"], "interpretation": answer}
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(answer)
        print(f"✓ {slug} -> {q['chart']} + {OUT}")

    print(f"\nDone. Ran: {', '.join(to_run)}.  Output: {OUT}")