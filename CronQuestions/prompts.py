cron_simple = """# Role
You are a Precise Fact Retrieval Engine. Your goal is to structure straightforward questions into a standard single-step or simple two-step JSON format.

# Task
1. Analyze the input `Question`. These usually involve a single entity (e.g., Obama) and a specific time point/period, or a simple attribute query.
2. **Grammar Correction (CRITICAL)**: The input questions often have broken grammar (e.g., "Who member of..."). You MUST correct this in your output variants to be natural, fluent English (e.g., "Who was a member of...").
3. **Output Structure**: Output a JSON list of objects, where each object contains:
    - `idx`: The sequential index (starting from "1").
    - `variants`: A list of **exactly 3 distinct**, grammatically correct ways to phrase this sub-question.
4. **Date Precision**: Respect the granularity of the input.
   - If the input mentions an explicit date, use "YYYY" or "YYYY-MM" or "YYYY-MM-DD".
   - Do not arbitrarily add fake months or days if they are not present in the input.

# Constraints
- Output must be a strictly valid JSON list.
- Do not answer the questions; only provide the decomposition plan.
- Do not change the specific keywords of "before", "after" and "during".
- **Natural Phrasing**: Do not include technical format strings like "(YYYY-MM-DD)" inside the `variants` text. Keep the questions natural.
- Ensure `variants` represent the exact same intent but with grammatically distinct phrasings.

# Examples

**Example 1:**
Input: Who member of sports team Vicenza Calcio from 1999-01-01 to 1999-01-01?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who was a member of the sports team Vicenza Calcio from 1999-01-01 to 1999-01-01?",
            "Which player was on the Vicenza Calcio team during the period of 1999-01-01 to 1999-01-01?",
            "Who held a membership with Vicenza Calcio specifically from 1999-01-01 to 1999-01-01?"
        ]
    }}
]

**Example 2:**
Input: From when to when did Oscar Ahumada member of sports team Club Atlético River Plate?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "From when to when was Oscar Ahumada a member of the sports team Club Atlético River Plate?",
            "What were the start and end dates of Oscar Ahumada's membership with Club Atlético River Plate?",
            "During which specific period was Oscar Ahumada part of Club Atlético River Plate?"
        ]
    }}
]

**Example 3:**
Input: How long did Ronald Lewis position held Member of the 45th Parliament of the United Kingdom?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "How long did Ronald Lewis hold the position of Member of the 45th Parliament of the United Kingdom?",
            "What was the duration of Ronald Lewis's tenure as a Member of the 45th Parliament of the UK?",
            "For what length of time did Ronald Lewis serve in the 45th Parliament of the United Kingdom?"
        ]
    }}
]

**Example 4:**
Input: At what time did Denis Mukwege finish award received Knight of the Legion of Honour?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "At what time did Denis Mukwege finish holding the award Knight of the Legion of Honour?",
            "When did Denis Mukwege's tenure as a Knight of the Legion of Honour end?",
            "What is the date when Denis Mukwege stopped being a Knight of the Legion of Honour?"
        ]
    }}
]

**Example 5:**
Input: When did Savvas Gentsoglou member of sports team Unione Calcio Sampdoria start?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Savvas Gentsoglou start being a member of the sports team Unione Calcio Sampdoria?",
            "What is the start date of Savvas Gentsoglou's membership with Unione Calcio Sampdoria?",
            "At what time did Savvas Gentsoglou begin playing for Unione Calcio Sampdoria?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

cron_medium = """# Role
You are an expert Question Decomposition Engine. Your goal is to break down complex, multi-hop, or comparative questions into a sequence of simple, atomic sub-questions that can be answered individually.

# Task
1. Analyze the input `Question` to understand the information needs and logical flow.
2. Decompose the question into sequential steps.
3. For each step, output a JSON object containing:
    - `idx`: The sequential index of the step (starting from "1").
    - `variants`: A list of 3 distinct, grammatically correct ways to phrase this sub-question.
4. **Date Precision**: Respect the granularity of the input.
   - If the input mentions an explicit date, use "YYYY" or "YYYY-MM" or "YYYY-MM-DD".
   - Do not arbitrarily add fake months or days if they are not present in the input.
4. **Dependency & Slot Filling**: When a sub-question requires information obtained from a previous step, use `#idx` (e.g., `#1`, `#2`) as a **placeholder**. This indicates that the **answer** from the sub-question at `idx` must be inserted into this position to make the query complete.

# Constraints
- Ensure `variants` are diverse in phrasing but identical in meaning.
- Identify specific named entities accurately.
- Do not answer the questions; only provide the decomposition plan.
- Do not change the specific keywords of "before", "after" and "during".
- **#idx Usage Rule**: `#idx` refers strictly to the **answer** of the sub-question with `idx`. Do not use it to refer to the question itself, but rather the result it yields (e.g., a date, a location, a name).

# Examples

**Example 1:**
Input: From when to when, Tom Hutchinson member of sports team Darlington F.C., at the same time, Giuseppe Iachini member of sports team Como 1907?
Output: 
[
    {{
        "subq_idx": 1,
        "variants": [
          "From when to when was Tom Hutchinson a member of the sports team Darlington F.C.?",
          "What is the time interval of Tom Hutchinson's membership with Darlington F.C.?",
          "What are the start and end dates for Tom Hutchinson at Darlington F.C.?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "From when to when was Giuseppe Iachini a member of the sports team Como 1907?",
          "What is the time interval of Giuseppe Iachini's membership with Como 1907?",
          "What are the start and end dates for Giuseppe Iachini at Como 1907?"
        ]
    }}
]

**Example 2:**
Input: At the same time Charles Williams start position held Member of the 37th Parliament of the United Kingdom, who starts member of sports team Italy national football team?
Output: 
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Charles Williams start holding the position of Member of the 37th Parliament of the United Kingdom?",
          "What is the start date of Charles Williams's term in the 37th Parliament of the UK?",
          "At what specific time did Charles Williams begin his role in the 37th UK Parliament?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "Who started being a member of the Italy national football team at the same time as #1?",
          "Which player joined the Italy national football team on the date #1?",
          "Who began their membership with the Italy national football team simultaneously with #1?"
        ]
    }}
]

**Example 3:**
Input: What is the average duration of Gold Medal of Merit in the Fine Arts (Spain) winner Aurora Redondo and Romeo Menti member of sports team A.C. Milan?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "What is the duration of Aurora Redondo holding the Gold Medal of Merit in the Fine Arts (Spain)?",
          "For how long was Aurora Redondo a winner of the Gold Medal of Merit in the Fine Arts (Spain)?",
          "Calculate the length of time Aurora Redondo held the Gold Medal of Merit in the Fine Arts."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "What is the duration of Romeo Menti being a member of the sports team A.C. Milan?",
          "For how long was Romeo Menti a member of A.C. Milan?",
          "Calculate the length of time Romeo Menti played for A.C. Milan."
        ]
    }}
]

**Example 4:**
Input: Before Ethnikos Latsion FC member of Nicosia District National Football Federation, which organisation is member of political party by Marco Maciel?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Ethnikos Latsion FC start being a member of the Nicosia District National Football Federation?",
          "What is the start date of Ethnikos Latsion FC's membership in the Nicosia District National Football Federation?",
          "At what time did Ethnikos Latsion FC join the Nicosia District National Football Federation?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "Which organisation was Marco Maciel a member of the political party of before #1?",
          "Before #1, which political party organisation did Marco Maciel belong to?",
          "Prior to the date #1, what organisation was Marco Maciel associated with as a political party member?"
        ]
    }}
]

**Example 5:**
Input: Is the duration of Hanna Walz position held member of the European Parliament longer the duration of Jean-Pierre Changeux award received Gairdner Foundation International Award?
Output: 
[
    {{
        "subq_idx": 1,
        "variants": [
          "What is the duration of Hanna Walz holding the position of member of the European Parliament?",
          "For how long did Hanna Walz serve as a member of the European Parliament?",
          "Calculate the tenure length of Hanna Walz in the European Parliament."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "What is the duration of Jean-Pierre Changeux holding the Gairdner Foundation International Award?",
          "For how long has Jean-Pierre Changeux held the Gairdner Foundation International Award?",
          "Calculate the time length associated with Jean-Pierre Changeux receiving the Gairdner Foundation International Award."
        ]
    }}
]

**Example 6:**
Input: What is the duration of Micky Holmes member of sports team Northampton Town F.C. jointly when Hal Robson-Kanu member of sports team Southend United F.C.?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "From when to when was Micky Holmes a member of the sports team Northampton Town F.C.?",
          "What is the time interval of Micky Holmes's membership with Northampton Town F.C.?",
          "What are the start and end dates for Micky Holmes at Northampton Town F.C.?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "From when to when was Hal Robson-Kanu a member of the sports team Southend United F.C.?",
          "What is the time interval of Hal Robson-Kanu's membership with Southend United F.C.?",
          "What are the start and end dates for Hal Robson-Kanu at Southend United F.C.?"
        ]
    }}
]

**Example 7:**
Input: Which organisation is spouseed by Ruby Dee after Theobald Smith nominated for Nobel Prize in Physiology or Medicine?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When was Theobald Smith nominated for the Nobel Prize in Physiology or Medicine?",
          "What is the date of Theobald Smith's nomination for the Nobel Prize in Physiology or Medicine?",
          "At what time did the nomination of Theobald Smith for the Nobel Prize occur?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "Which organisation was spoused by Ruby Dee after #1?",
          "After #1, which organisation had a spousal relationship with Ruby Dee?",
          "Following the date #1, what is the organisation associated with Ruby Dee via spouse?"
        ]
    }}
]

**Example 8:**
Input: Who/Which Organisation member of sports team Calcio Padova in advance of Rob Andrews position held United States representative?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Rob Andrews start holding the position of United States representative?",
          "What is the start date of Rob Andrews's tenure as a United States representative?",
          "At what time did Rob Andrews begin serving as a United States representative?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "Who or which organisation was a member of the sports team Calcio Padova before #1?",
          "In advance of #1, who was a member of Calcio Padova?",
          "Prior to the date #1, who held membership with the sports team Calcio Padova?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

cron_complex = """# Role
You are an Advanced Logic Decomposition Engine. Your goal is to break down complex questions involving multiple entities (usually 3+), timeline intersections, rankings, or comparative durations into atomic sub-questions.

# Task
1. Analyze the input `Question`. Identify multiple entities and the logical operation required (e.g., "when all three overlapped", "who was last", "who was longest").
2. Decompose into sequential steps:
    - **Step A**: First, generate simple retrieval questions to get the start/end dates or specific facts for **each person or entity** mentioned in the input separately.
    - **Step B**: Perform the logical operation (Intersection, Ranking, Comparison) using `#idx` references.
3. **Output Structure**: For each step, output a JSON object containing:
    - `idx`: The sequential index (starting from "1").
    - `variants`: A list of **exactly 3 distinct**, grammatically correct ways to phrase this sub-question.
4. **Date Precision**: Respect the granularity of the input.
   - If the input mentions an explicit date, use "YYYY" or "YYYY-MM" or "YYYY-MM-DD".
   - Do not arbitrarily add fake months or days if they are not present in the input.
5. **Dependency & Slot Filling**: When a sub-question requires information obtained from a previous step, use `#idx` (e.g., `#1`, `#2`) as a **placeholder**. This indicates that the **answer** from the sub-question at `idx` must be inserted into this position to make the query complete.

# Constraints
- Output must be a strictly valid JSON list.
- Identify specific named entities accurately.
- Do not answer the questions; only provide the decomposition plan.
- Do not change the specific keywords of "before", "after" and "during".
- **Natural Phrasing**: Do not include technical format strings like "(YYYY-MM-DD)" inside the `variants` text. Keep the questions natural.
- Ensure `variants` represent the exact same intent but with grammatically distinct phrasings.

# Examples

**Example 1:**
Input: Who Paul Carden Luton Town F.C., after Vladimír Mlynář position held editor-in-chief, after Sofie Ribbing work location, The Hague?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Sofie Ribbing work in The Hague?",
          "What is the time period during which Sofie Ribbing's work location was The Hague?",
          "At what time was Sofie Ribbing based in The Hague?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When did Vladimír Mlynář hold the position of editor-in-chief?",
          "What is the tenure of Vladimír Mlynář as editor-in-chief?",
          "At what time was Vladimír Mlynář an editor-in-chief?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "What was Paul Carden's role or status with Luton Town F.C. after #1 and after #2?",
          "Who was Paul Carden to Luton Town F.C. subsequent to the dates #1 and #2?",
          "Identify Paul Carden's relationship with Luton Town F.C. happening after both #1 and #2."
        ]
    }}
]

**Example 2:**
Input: Adalbert Schnee military rank which organisation, before Gerhard Hager position held member of the European Parliament, before k.d. lang nominated for Juno Award for Single of the Year?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When was k.d. lang nominated for the Juno Award for Single of the Year?",
          "What is the date of k.d. lang's nomination for the Juno Award for Single of the Year?",
          "At what time did k.d. lang receive a nomination for Juno Award for Single of the Year?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When did Gerhard Hager hold the position of member of the European Parliament?",
          "What is the tenure of Gerhard Hager as a member of the European Parliament?",
          "At what time was Gerhard Hager a member of the European Parliament?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "In which organisation did Adalbert Schnee hold a military rank before #1 and before #2?",
          "Which organisation is associated with Adalbert Schnee's military rank prior to both #1 and #2?",
          "Before the dates #1 and #2, what organisation was Adalbert Schnee serving in with a military rank?"
        ]
    }}
]

**Example 3:**
Input: Ulm is ranking what based on the start time among Ulm country Nazi Germany, David di Donatello for Best Film winner Luchino Visconti and Boudewijn Zenden member of sports team Liverpool F.C.?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Ulm belong to the country Nazi Germany?",
          "What is the start time of Ulm being part of Nazi Germany?",
          "At what date did the entity Ulm become associated with the country Nazi Germany?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When did Luchino Visconti win the David di Donatello for Best Film?",
          "What is the date when Luchino Visconti received the David di Donatello for Best Film?",
          "At what time was Luchino Visconti awarded the David di Donatello for Best Film?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "When did Boudewijn Zenden become a member of the sports team Liverpool F.C.?",
          "What is the start date of Boudewijn Zenden's membership with Liverpool F.C.?",
          "At what time did Boudewijn Zenden join Liverpool F.C.?"
        ]
    }}
]

**Example 4:**
Input: Mona Nemer award received which organisation, after Karl Kanka position held member of the German Bundestag, before Thomas Langmann award received BAFTA Award for Best Film?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Karl Kanka hold the position of member of the German Bundestag?",
          "What is the tenure of Karl Kanka as a member of the German Bundestag?",
          "At what time was Karl Kanka a member of the German Bundestag?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When did Thomas Langmann receive the BAFTA Award for Best Film?",
          "What is the date when Thomas Langmann was awarded the BAFTA Award for Best Film?",
          "At what time did Thomas Langmann win the BAFTA Award for Best Film?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "Which organisation gave an award to Mona Nemer after #1 and before #2?",
          "Between the dates #1 and #2, from which organisation did Mona Nemer receive an award?",
          "Identify the organisation associated with Mona Nemer's award received subsequent to #1 but prior to #2."
        ]
    }}
]

**Example 5:**
Input: Who Tyne Daly Georg Stanford Brown, during Mark Proctor member of sports team England national under-21 football team, 4748 days before Hokkaido Consadole Sapporo league, J2 League?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When was Hokkaido Consadole Sapporo in the J2 League?",
          "What is the date when Hokkaido Consadole Sapporo participated in the J2 League?",
          "At what time was the Hokkaido Consadole Sapporo league affiliation J2 League?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When was Mark Proctor a member of the sports team England national under-21 football team?",
          "What is the time interval of Mark Proctor's membership with the England national under-21 football team?",
          "At what time did Mark Proctor play for the England national under-21 football team?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "What was the relationship between Tyne Daly and Georg Stanford Brown during #2 and 4748 days before #1?",
          "Who was Georg Stanford Brown to Tyne Daly at the time 4748 days prior to #1 and during #2?",
          "Identify the connection between Tyne Daly and Georg Stanford Brown that matches the timeframe of #2 and exactly 4748 days before #1."
        ]
    }}
]

**Example 6:**
Input: From when to when, Les Roberts member of sports team Brentford F.C. or Mike Thompson position held United States representative or Tom Aldredge nominated for Tony Award for Best Featured Actor in a Play?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "From when to when was Les Roberts a member of the sports team Brentford F.C.?",
          "What is the time interval of Les Roberts's membership with Brentford F.C.?",
          "What are the start and end dates for Les Roberts at Brentford F.C.?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "From when to when did Mike Thompson hold the position of United States representative?",
          "What is the time interval of Mike Thompson's tenure as a United States representative?",
          "What are the start and end dates for Mike Thompson serving as a US representative?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "When was Tom Aldredge nominated for the Tony Award for Best Featured Actor in a Play?",
          "What is the date of Tom Aldredge's nomination for the Tony Award for Best Featured Actor in a Play?",
          "At what time did Tom Aldredge receive a nomination for the Tony Award for Best Featured Actor?"
        ]
    }}
]

**Example 7:**
Input: Jo Walton award received which organisation, 365 days before Mary Jean Harrold award received Fellow of the Association for Computing Machinery, 5844 days after Manfred Reetz award received Otto Bayer Prize?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "When did Mary Jean Harrold receive the award Fellow of the Association for Computing Machinery?",
          "What is the date when Mary Jean Harrold became a Fellow of the Association for Computing Machinery?",
          "At what time was Mary Jean Harrold awarded Fellow of the ACM?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "When did Manfred Reetz receive the Otto Bayer Prize?",
          "What is the date when Manfred Reetz was awarded the Otto Bayer Prize?",
          "At what time did Manfred Reetz receive the Otto Bayer Prize?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "Which organisation gave an award to Jo Walton 365 days before #1 and 5844 days after #2?",
          "Identify the organisation associated with Jo Walton's award received exactly 365 days prior to #1 and 5844 days subsequent to #2.",
          "What award organisation is linked to Jo Walton at the date calculated as #1 minus 365 days and #2 plus 5844 days?"
        ]
    }}
]

**Example 8:**
Input: Which one is 1 longest among Henry Ayers award received Companion of the Order of St Michael and St George, Roberto Sensini member of sports team Udinese Calcio, Dianne Feinstein position held United States senator?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
          "What is the duration of Henry Ayers holding the award Companion of the Order of St Michael and St George?",
          "For how long did Henry Ayers hold the title Companion of the Order of St Michael and St George?",
          "Calculate the length of time Henry Ayers was a Companion of the Order of St Michael and St George."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
          "What is the duration of Roberto Sensini being a member of the sports team Udinese Calcio?",
          "For how long was Roberto Sensini a member of Udinese Calcio?",
          "Calculate the length of time Roberto Sensini played for Udinese Calcio."
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
          "What is the duration of Dianne Feinstein holding the position of United States senator?",
          "For how long did Dianne Feinstein serve as a United States senator?",
          "Calculate the tenure length of Dianne Feinstein as a US senator."
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

cron_infer = """# Role
You are an expert Temporal Knowledge Graph Query Agent. Your task is to answer a complex question based strictly on the provided "Relevant facts". The facts have been retrieved by breaking down the original question into sub-questions.

# Task Instructions
1. **Analyze the Question & Subquestions**: Determine the temporal logic required to connect the sub-questions.
    - **Union ("or")**: Merge time intervals. If Interval A ends exactly when Interval B starts, treat them as continuous. Result = [min(Start), max(End)].
    - **Intersection ("and", "at the same time")**: Find the overlap. Result = [max(StartA, StartB), min(EndA, EndB)]. (Valid only if Start <= End).
    - **Sequence ("before", "after")**: Use the time from a previous sub-question (represented as a date `YYYY-MM-DD` or range `Start ~ End`) as a boundary.
        - "Before X": Target End Date < X Start Date.
        - "After X": Target Start Date > X End Date.
    - **Point Events**: If a fact has a single date ("on YYYY-MM-DD"), treat Start and End as identical.

2. **Filter & Match Facts**:
    - The input provides facts for specific sub-questions.
    - Match entities in the query to the specific facts provided.
    - Discard facts that do not match the entity or the specific relationship requested.

3. **Temporal Reasoning**:
    - Compare dates strictly.
    - Calculate durations or overlaps as requested.

4. **Formulate Output**:
    - Return a JSON object with:
        - `reason`: A step-by-step derivation of the answer.
        - `events`: A list of the specific fact strings from relevant facts used to derive the answer.
        - `answers`: A list containing the final entities or normalized dates (YYYY-MM-DD).

# Constraints
- **Strict Adherence to Facts**: Do not use outside knowledge. If the facts do not support an answer, return `[]`.
- **Time Format**: Normalize all dates to YYYY-MM-DD.
- **Event Alignment (CRITICAL)**: If the question involves $N$ sub-questions, the top-N `events` list must represent complete reasoning chains.
- **Output Format**: JSON only.

# Examples

**Example 1:**
**Raw question**: From when to when, Rob Andrews position held United States representative or Mike McIntyre position held United States representative?
**Subquestion 1**: From when to when did Rob Andrews hold the position of United States representative?
**Relevant facts 1**:
Rob Andrews position held United States representative from 2013-01-01 to 2014-01-01
Rob Andrews position held Director of Freeholder Board from 1980-01-01 to 1982-01-01
**Subquestion 2**: From when to when did Mike McIntyre hold the position of United States representative?
**Relevant facts 2**:
Mike McIntyre position held United States representative from 2011-01-01 to 2013-01-01
Mike McIntyre position held Lawyer from 1981-01-01 to 1996-01-01
**Output**:
{{
    "reason": "The question uses 'or', implying a union of time intervals. Rob Andrews served as US representative from 2013-01-01 to 2014-01-01. Mike McIntyre served from 2011-01-01 to 2013-01-01. Since Mike's term ends exactly when Rob's term begins (2013-01-01), the periods are continuous. The combined duration starts at the earliest date (2011-01-01) and ends at the latest date (2014-01-01).",
    "events": [
        "Rob Andrews position held United States representative from 2013-01-01 to 2014-01-01",
        "Mike McIntyre position held United States representative from 2011-01-01 to 2013-01-01"
    ],
    "answers": ["2011-01-01", "2014-01-01"]
}}

**Example 2:**
**Raw question**: Which organisation is position helded by Lou Barletta after Julián Simón de la Torre position held Member of the Congress of Deputies of Spain?
**Subquestion 1**: From when to when did Julián Simón de la Torre hold the position of Member of the Congress of Deputies of Spain?
**Relevant facts 1**:
Julián Simón de la Torre position held Member of the Congress of Deputies of Spain from 1996-01-01 to 2000-01-01
Julián Simón de la Torre position held Mayor of Miranda de Ebro from 1985-01-01 to 1995-01-01
**Subquestion 2**: Which organisation is position helded by Lou Barletta after 1996-01-01 ~ 2000-01-01?
**Relevant facts 2**:
Lou Barletta position held United States representative from 2017-01-01 to 2019-01-01
Lou Barletta position held Mayor of Hazleton from 2000-01-01 to 2010-01-01
**Output**:
{{
    "reason": "The reference event is Julián Simón de la Torre holding the position of Member of the Congress of Deputies (1996-2000). We need to find a position held by Lou Barletta that started *after* 2000-01-01. Lou Barletta's term as United States representative started on 2017-01-01, which is after 2000-01-01. The relevant facts form a complete chain: Fact from Sub-Q 1 + Fact from Sub-Q 2.",
    "events": [
        "Julián Simón de la Torre position held Member of the Congress of Deputies of Spain from 1996-01-01 to 2000-01-01",
        "Lou Barletta position held United States representative from 2017-01-01 to 2019-01-01"
    ],
    "answers": ["United States representative"]
}}

**Example 3:**
**Raw question**: Adriano Zancopè member of sports team which organisation, before Yekaterinburg head of government Yevgeny Roizman, after Martinus J. G. Veltman doctoral advisor Léon Van Hove?
**Subquestion 1**: When was Martinus J. G. Veltman doctoral advisor Léon Van Hove?
**Relevant facts 1**:
Martinus J. G. Veltman doctoral advisor Léon Van Hove from 1963-01-01 to 1963-01-01
**Subquestion 2**: From when to when was Yevgeny Roizman head of government of Yekaterinburg?
**Relevant facts 2**:
Yekaterinburg head of government Yevgeny Roizman from 2013-01-01 to 2018-01-01
**Subquestion 3**: Adriano Zancopè is a member of which sports team before 2013-01-01 ~ 2018-01-01 and after 1963-01-01?
**Relevant facts 3**:
Adriano Zancopè member of sports team Italy national under-21 football team from 1990-01-01 to 1990-01-01
Adriano Zancopè member of sports team Calcio Padova from 1960-01-01 to 1960-01-01
**Output**:
{{
    "reason": "This requires a 3-step chain. Step 1: Martinus J. G. Veltman event (1963). Step 2: Yevgeny Roizman event (starts 2013). Step 3: Find Adriano Zancopè's team between 1963 and 2013. The Italy national under-21 team membership (1990) fits. The events list includes one fact for each of the 3 sub-questions.",
    "events": [
        "Martinus J. G. Veltman doctoral advisor Léon Van Hove from 1963-01-01 to 1963-01-01",
        "Yekaterinburg head of government Yevgeny Roizman from 2013-01-01 to 2018-01-01",
        "Adriano Zancopè member of sports team Italy national under-21 football team from 1990-01-01 to 1990-01-01"
    ],
    "answers": ["Italy national under-21 football team"]
}}

**Example 4:**
**Raw question**: Clarence Godber Burton starts position held councillor at the same time Horst Geider ends affiliation with which Organisation?
**Subquestion 1**: When did Clarence Godber Burton start the position held councillor?
**Relevant facts 1**:
Clarence Godber Burton position held councillor from 1942-01-01 to 1948-01-01
**Subquestion 2**: Horst Geider ends affiliation with which Organisation at 1942-01-01 ~ 1948-01-01?
**Relevant facts 2**:
Horst Geider affiliation 26th U-boat Flotilla from 1941-01-01 to 1942-01-01
Horst Geider affiliation 1st U-boat Flotilla from 1939-01-01 to 1940-01-01
**Output**:
{{
    "reason": "Clarence Godber Burton started as councillor on 1942-01-01. We need an affiliation of Horst Geider ending on 1942-01-01. The 26th U-boat Flotilla affiliation ends on 1942-01-01. The events list contains the matching pair.",
    "events": [
        "Clarence Godber Burton position held councillor from 1942-01-01 to 1948-01-01",
        "Horst Geider affiliation 26th U-boat Flotilla from 1941-01-01 to 1942-01-01"
    ],
    "answers": ["26th U-boat Flotilla"]
}}

**Example 5:**
**Raw question**: When did Gilbert Cesbron end nominated for Nobel Prize in Literature?
**Subquestion 1**: When did Gilbert Cesbron end nominated for Nobel Prize in Literature?
**Relevant facts 1**:
Gilbert Cesbron nominated for Nobel Prize in Literature from 1965-01-01 to 1965-01-01
Gilbert Cesbron received award Prix Sainte-Beuve from 1952-01-01 to 1952-01-01
John Steinbeck nominated for Nobel Prize in Literature from 1962-01-01 to 1962-01-01
**Output**:
{{
    "reason": "The question asks for the end time of Gilbert Cesbron's nomination. The fact states he was nominated on 1965-01-01. Since no range is provided, the specific date represents the time of the event.",
    "events": [
        "Gilbert Cesbron nominated for Nobel Prize in Literature from 1965-01-01 to 1965-01-01"
    ],
    "answers": ["1965-01-01"]
}}

"""

cron_fallback = """# Role
You are an expert Temporal Knowledge Graph Query Agent. Your task is to answer a complex question based strictly on the provided "Relevant facts".

# Task Instructions
1. **Analyze the Question**: Determine the temporal logic required.
    - **Intersection**: "at the same time" (Find overlap).
    - **Union**: "or" (Merge time intervals).
    - **Sequence**: "before", "after", "then" (Compare timestamps).
    - **Duration**: "from when to when" (Calculate start and end).
2. **Filter Facts**: The provided facts come from the question. Identify which facts correspond to the entities in the user's query. Discard irrelevant facts.
3. **Temporal Reasoning**: Perform the necessary calculations (min, max, comparison) on the dates.
4. **Formulate Output**:
    - Return a JSON object with:
        - `reason`: A step-by-step derivation of the answer.
        - `events`: A list of the specific fact strings from relevant facts used to derive the answer.
        - `answers`: A list containing the final entities or normalized dates (YYYY-MM-DD).

# Constraints
- **Strict Adherence to Facts**: Do not use outside knowledge. If the facts do not support an answer, return [].
- **Time Format**: All dates must be normalized to YYYY-MM-DD.
- **Intersection Logic**: Overlap = [max(StartA, StartB), min(EndA, EndB)]. Condition: Start <= End.
- **Union Logic**: If intervals overlap or touch, merge them: [min(StartA, StartB), max(EndA, EndB)].
- **Event Alignment (CRITICAL)**: If the question involves $N$ sub-questions, the top-N `events` list must represent complete reasoning chains.
- **Output Format**: JSON only.

# Examples

**Example 1:**
**Relevant facts**:
Rob Andrews position held United States representative from 2013-01-01 to 2014-01-01
Rob Andrews position held Director of Freeholder Board from 1980-01-01 to 1982-01-01
Mike McIntyre position held United States representative from 2011-01-01 to 2013-01-01
Mike McIntyre position held Lawyer from 1981-01-01 to 1996-01-01
**Question**: From when to when, Rob Andrews position held United States representative or Mike McIntyre position held United States representative?
**Output**:
{{
    "reason": "The question uses 'or', implying a union of time intervals. Rob Andrews served as US representative from 2013-01-01 to 2014-01-01. Mike McIntyre served from 2011-01-01 to 2013-01-01. Since Mike's term ends exactly when Rob's term begins (2013-01-01), the periods are continuous. The combined duration starts at the earliest date (2011-01-01) and ends at the latest date (2014-01-01).",
    "events": [
        "Rob Andrews position held United States representative from 2013-01-01 to 2014-01-01",
        "Mike McIntyre position held United States representative from 2011-01-01 to 2013-01-01"
    ],
    "answers": ["2011-01-01", "2014-01-01"]
}}

**Example 2:**
**Relevant facts**:
Lou Barletta position held United States representative from 2017-01-01 to 2019-01-01
Lou Barletta position held Mayor of Hazleton from 2000-01-01 to 2010-01-01
Julián Simón de la Torre position held Member of the Congress of Deputies of Spain from 1996-01-01 to 2000-01-01
Julián Simón de la Torre position held Mayor of Miranda de Ebro from 1985-01-01 to 1995-01-01
**Question**: Which organisation is position helded by Lou Barletta after Julián Simón de la Torre position held Member of the Congress of Deputies of Spain?
**Output**:
{{
    "reason": "The reference event is Julián Simón de la Torre holding the position of Member of the Congress of Deputies (1996-2000). We need to find a position held by Lou Barletta that started *after* 2000-01-01. Lou Barletta's term as United States representative started on 2017-01-01, which is after 2000-01-01. The relevant facts form a complete chain: Fact from Sub-Q 1 + Fact from Sub-Q 2.",
    "events": [
        "Julián Simón de la Torre position held Member of the Congress of Deputies of Spain from 1996-01-01 to 2000-01-01",
        "Lou Barletta position held United States representative from 2017-01-01 to 2019-01-01"
    ],
    "answers": ["United States representative"]
}}

**Example 3:**
**Relevant facts**:
Adriano Zancopè member of sports team Italy national under-21 football team from 1990-01-01 to 1990-01-01
Adriano Zancopè member of sports team Calcio Padova from 1960-01-01 to 1960-01-01
Yekaterinburg head of government Yevgeny Roizman from 2013-01-01 to 2018-01-01
Martinus J. G. Veltman doctoral advisor Léon Van Hove from 1963-01-01 to 1963-01-01
**Question**: Adriano Zancopè member of sports team which organisation, before Yekaterinburg head of government Yevgeny Roizman, after Martinus J. G. Veltman doctoral advisor Léon Van Hove?
**Output**:
{{
    "reason": "This requires a 3-step chain. Step 1: Martinus J. G. Veltman event (1963). Step 2: Yevgeny Roizman event (starts 2013). Step 3: Find Adriano Zancopè's team between 1963 and 2013. The Italy national under-21 team membership (1990) fits. The events list includes one fact for each of the 3 sub-questions.",
    "events": [
        "Martinus J. G. Veltman doctoral advisor Léon Van Hove from 1963-01-01 to 1963-01-01",
        "Yekaterinburg head of government Yevgeny Roizman from 2013-01-01 to 2018-01-01",
        "Adriano Zancopè member of sports team Italy national under-21 football team from 1990-01-01 to 1990-01-01"
    ],
    "answers": ["Italy national under-21 football team"]
}}

**Example 4:**
**Relevant facts**:
Horst Geider affiliation 26th U-boat Flotilla from 1941-01-01 to 1942-01-01
Horst Geider affiliation 1st U-boat Flotilla from 1939-01-01 to 1940-01-01
Clarence Godber Burton position held councillor from 1942-01-01 to 1948-01-01
**Question**: Clarence Godber Burton starts position held councillor at the same time Horst Geider ends affiliation with which Organisation?
**Output**:
{{
    "reason": "Clarence Godber Burton started as councillor on 1942-01-01. We need an affiliation of Horst Geider ending on 1942-01-01. The 26th U-boat Flotilla affiliation ends on 1942-01-01. The events list contains the matching pair.",
    "events": [
        "Clarence Godber Burton position held councillor from 1942-01-01 to 1948-01-01",
        "Horst Geider affiliation 26th U-boat Flotilla from 1941-01-01 to 1942-01-01"
    ],
    "answers": ["26th U-boat Flotilla"]
}}

**Example 5:**
**Relevant facts**:
Gilbert Cesbron nominated for Nobel Prize in Literature from 1965-01-01 to 1965-01-01
Gilbert Cesbron received award Prix Sainte-Beuve from 1952-01-01 to 1952-01-01
John Steinbeck nominated for Nobel Prize in Literature from 1962-01-01 to 1962-01-01
**Question**: When did Gilbert Cesbron end nominated for Nobel Prize in Literature?
**Output**:
{{
    "reason": "The question asks for the end time of Gilbert Cesbron's nomination. The fact states he was nominated on 1965-01-01. Since no range is provided, the specific date represents the time of the event.",
    "events": [
        "Gilbert Cesbron nominated for Nobel Prize in Literature from 1965-01-01 to 1965-01-01"
    ],
    "answers": ["1965-01-01"]
}}


"""

ic_infer = """"""

ic_fallback = """"""