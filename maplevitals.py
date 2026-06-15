import os
import pandas as pd
from dotenv import load_dotenv
from anthropic import Anthropic

# 1) load the API key from .env
load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 2) load the data
df=pd.read_csv("./data/health_canada.csv")

# 3) Build a compact profile of the data (Never send the whole csv because of token limits + cost)
profile=f"""
Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns.

Columns and types:
{df.dtypes.to_string()}

First 5 rows:
{df.head().to_string()}

Numeric summary:
{df.describe().to_string()}

"""

# 4) Ask the LLM to describe it in plain English

prompt = f""" You are a data analyst. Here is a profile of a Canadian public-health dataset:
{profile}
In plain English, tell me:
1. What this dataset appears to be about.
2. What each column likely means.
3. Three interesting questions a public-health analyst could ask it.
Keep it concise."""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    temperature=0,
    messages=[{"role": "user", "content": prompt}],
)
print(response.content[0].text)


'''
# Experiment 1: Change the temperature to 1 to see how the output gets more varied/creative
prompt = f""" You are a data analyst. Here is a profile of a Canadian public-health dataset:
{profile}
In plain English, tell me:
1. What this dataset appears to be about.
2. What each column likely means.
3. Three interesting questions a public-health analyst could ask it.
Keep it concise."""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    temperature=1,
    messages=[{"role": "user", "content": prompt}],
)
print(response.content[0].text)
'''

'''
# Experiment 2: change the prompt

prompt = f""" You are a data analyst. Here is a profile of a Canadian public-health dataset:

{profile}

In plain English, tell me:
1. Which single column would be most useful for studying diabetes trends, and why?
Keep it concise."""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    temperature=0,
    messages=[{"role": "user", "content": prompt}],
)
print(response.content[0].text)

'''

'''
# Experiment 3: setting up the role

prompt = f""" You are a data analyst. Here is a profile of a Canadian public-health dataset:
{profile}
In plain English, tell me:
1. What this dataset appears to be about.
2. What each column likely means.
3. Three interesting questions a public-health analyst could ask it.
Keep it concise."""

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    temperature=0,
    messages=[{"role": "user", "content": prompt}],
    system="You are a careful public-health data analyst.",
)
print(response.content[0].text)
'''

