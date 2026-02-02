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

icews_actor_simple = """# Role
You are a Precise Fact Retrieval Engine. Your goal is to structure straightforward questions into a standard single-step or simple two-step JSON format.

# Task
1.  **Analyze the Question**: These questions usually involve political affiliations, government positions, or entity relationships constrained by specific time points, periods, or durations.
2.  **Output Structure**: Output a JSON list of objects, where each object contains:
    * `idx`: The sequential index (starting from "1").
    * `variants`: A list of **exactly 3 distinct**, grammatically correct ways to phrase this sub-question.
3.  **Date Precision**: Respect the granularity of the input.
    * Do not change the specific keywords "beginning of time" or "end of time".
    * If the input mentions an explicit date, use the exact format provided (usually "YYYY-MM-DD").

# Constraints
* Output must be a strictly valid JSON list.
* Do not answer the questions; only provide the decomposition plan.
* **Natural Phrasing**: Do not include technical format strings like "(YYYY-MM-DD)" inside the `variants` text. Keep the questions conversational.
* Ensure `variants` represent the exact same intent but with grammatically distinct phrasings.

# Examples

**Example 1:**
Input: At what point did Max Bradford cease his affiliation with the major governing party in New Zealand?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Max Bradford end his affiliation with the major governing party in New Zealand?",
            "At what point in time did Max Bradford cease his affiliation with the major governing party in New Zealand?",
            "What is the date when Max Bradford stopped being affiliated with the major governing party in New Zealand?"
        ]
    }}
]

**Example 2:**
Input: How long did Jorge Heine Affiliation To Ministry of National Assets?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "How long was Jorge Heine affiliated to the Ministry of National Assets?",
            "What was the duration of Jorge Heine's Affiliation To the Ministry of National Assets?",
            "For what length of time did Jorge Heine maintain an Affiliation To the Ministry of National Assets?"
        ]
    }}
]

**Example 3:**
Input: Who Affiliation To National Democratic Party from beginning of time to 2006-12-31?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who had an Affiliation To the National Democratic Party from beginning of time to 2006-12-31?",
            "Which person was affiliated to the National Democratic Party in the period from beginning of time to 2006-12-31?",
            "Who held an Affiliation To the National Democratic Party starting from beginning of time until 2006-12-31?"
        ]
    }}
]

**Example 4:**
Input: Which organisation is Affiliation To by Khamliang Phonsena from beginning of time to end of time?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Which organisation was Khamliang Phonsena affiliated to from beginning of time to end of time?",
            "What organisation had an Affiliation To by Khamliang Phonsena for the period from beginning of time to end of time?",
            "To which organisation did Khamliang Phonsena maintain an Affiliation To from beginning of time to end of time?"
        ]
    }}
]

**Example 5:**
Input: Ministry of Agriculture is Affiliation To by who from 2005-01-01 to 2010-01-01?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who had an Affiliation To the Ministry of Agriculture from 2005-01-01 to 2010-01-01?",
            "By whom was the Ministry of Agriculture Affiliation To during the period of 2005-01-01 to 2010-01-01?",
            "Which person maintained an Affiliation To the Ministry of Agriculture between 2005-01-01 and 2010-01-01?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

icews_actor_medium = """# Role
You are an expert Question Decomposition Engine. Your goal is to break down complex, multi-hop, or comparative questions into a sequence of simple, atomic sub-questions that can be answered individually.

# Task
1.  **Analyze the Question**: Understand the logical flow, which usually involves:
    * **Union/Intersection**: "From when to when... A or B", "At the same time...".
    * **Duration Calculation**: "Total duration", "Average duration".
    * **Comparison**: "Is the duration... shorter/longer...".
    * **Dependency**: "During X, who...", "After X...".
2.  **Decompose**: Break the question into sequential steps.
3.  **Output Structure**: For each step, output a JSON object containing:
    * `idx`: The sequential index (starting from "1").
    * `variants`: A list of **exactly 3 distinct**, grammatically correct ways to phrase this sub-question.
4.  **Dependency & Slot Filling**: When a sub-question requires information obtained from a previous step, use `#idx` (e.g., `#1`, `#2`) as a **placeholder**.
    * **Example**: If Step 1 finds a time period, Step 2 should ask "Who was affiliated... during #1?".

# Constraints
* **Date Precision**:
    * Do **not** change the specific keywords "beginning of time" or "end of time".
    * If the input mentions an explicit date, use "YYYY-MM-DD".
* **#idx Usage Rule**: `#idx` refers strictly to the **answer** of the sub-question with `idx` (e.g., a date, a duration, a person).
* **Entity Precision**: Preserve specific entity names exactly as they appear (e.g., "Information / Communication / Transparency NGOs (United States)").
* **Natural Phrasing**: Do not include technical format strings inside the `variants` text. Keep the questions conversational.

# Examples

**Example 1:**
Input: From when to when, Hauser Center for Nonprofit Organizations Affiliation To Information / Communication / Transparency NGOs (United States) or Elaine Lan Chao Affiliation To U.S. Republican Party?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "From when to when was the Hauser Center for Nonprofit Organizations affiliated with Information / Communication / Transparency NGOs (United States)?",
            "What is the time period of the Hauser Center for Nonprofit Organizations' affiliation to Information / Communication / Transparency NGOs (United States)?",
            "When did the Hauser Center for Nonprofit Organizations maintain an affiliation to Information / Communication / Transparency NGOs (United States)?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "From when to when was Elaine Lan Chao affiliated with the U.S. Republican Party?",
            "What is the time period of Elaine Lan Chao's affiliation to the U.S. Republican Party?",
            "When did Elaine Lan Chao maintain an affiliation to the U.S. Republican Party?"
        ]
    }}
]

**Example 2:**
Input: How long is the total duration of Atta Mohammed Nur Affiliation To Northern Alliance and Kennedy Sakeni Affiliation To Ministry of Home Affairs?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "How long was Atta Mohammed Nur affiliated with the Northern Alliance?",
            "What was the duration of Atta Mohammed Nur's affiliation to the Northern Alliance?",
            "Calculate the length of time Atta Mohammed Nur held an affiliation to the Northern Alliance."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "How long was Kennedy Sakeni affiliated with the Ministry of Home Affairs?",
            "What was the duration of Kennedy Sakeni's affiliation to the Ministry of Home Affairs?",
            "Calculate the length of time Kennedy Sakeni held an affiliation to the Ministry of Home Affairs."
        ]
    }}
]

**Example 3:**
Input: What is the average duration of Attorney General Ruddock Affiliation To Opposition Major Party (Out Of Government) (Australia) and Platinum Group Metals Ltd Affiliation To Heavy Industrial / Chemical Business (Multi-National Corporations)?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "What is the duration of Attorney General Ruddock's affiliation with the Opposition Major Party (Out Of Government) (Australia)?",
            "For how long was Attorney General Ruddock affiliated to the Opposition Major Party (Out Of Government) (Australia)?",
            "Calculate the time length of Attorney General Ruddock's affiliation to the Opposition Major Party (Australia)."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "What is the duration of Platinum Group Metals Ltd's affiliation with Heavy Industrial / Chemical Business (Multi-National Corporations)?",
            "For how long was Platinum Group Metals Ltd affiliated to Heavy Industrial / Chemical Business (Multi-National Corporations)?",
            "Calculate the time length of Platinum Group Metals Ltd's affiliation to Heavy Industrial / Chemical Business."
        ]
    }}
]

**Example 4:**
Input: At the same time André Kimbuta Affiliation To People's Party for Reconstruction and Democracy, in which organisation Manila Times Affiliation To?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When was André Kimbuta affiliated with the People's Party for Reconstruction and Democracy?",
            "What is the time period of André Kimbuta's affiliation to the People's Party for Reconstruction and Democracy?",
            "At what time did André Kimbuta hold an affiliation to the People's Party for Reconstruction and Democracy?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which organisation was the Manila Times affiliated with during the time #1?",
            "To which organisation did the Manila Times have an affiliation at the same time as #1?",
            "Identify the organisation affiliated with the Manila Times during the period #1."
        ]
    }}
]

**Example 5:**
Input: Who Affiliation To Medical / Health / Pharmeceutical Business (Multi-National Corporations) during Stefan Sofiyanski Affiliation To Sofia?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When was Stefan Sofiyanski affiliated with Sofia?",
            "What is the time period of Stefan Sofiyanski's affiliation to Sofia?",
            "At what time did Stefan Sofiyanski hold an affiliation to Sofia?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was affiliated with Medical / Health / Pharmeceutical Business (Multi-National Corporations) during #1?",
            "Which entity held an affiliation to Medical / Health / Pharmeceutical Business (Multi-National Corporations) throughout the period #1?",
            "Identify the person or entity affiliated to Medical / Health / Pharmeceutical Business (Multi-National Corporations) in the timeframe #1."
        ]
    }}
]

**Example 6:**
Input: Is the duration of José de Gregorio Affiliation To Central Bank of Chile shorter the duration of Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco)?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "What is the duration of José de Gregorio's affiliation with the Central Bank of Chile?",
            "For how long was José de Gregorio affiliated to the Central Bank of Chile?",
            "Calculate the length of time José de Gregorio held an affiliation to the Central Bank of Chile."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "What is the duration of Hightech Payment Systems' affiliation with Consulting / Financial Services Business (Morocco)?",
            "For how long was Hightech Payment Systems affiliated to Consulting / Financial Services Business (Morocco)?",
            "Calculate the length of time Hightech Payment Systems held an affiliation to Consulting / Financial Services Business (Morocco)."
        ]
    }}
]

**Example 7:**
Input: Who Affiliation To Elite (Comoros) at the same start and end time Khalil Fleihan start and end Affiliation To Daily Star?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "What are the start and end dates of Khalil Fleihan's affiliation with the Daily Star?",
            "From when to when was Khalil Fleihan affiliated to the Daily Star?",
            "Identify the specific start and end times for Khalil Fleihan's affiliation to the Daily Star."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was affiliated with Elite (Comoros) during the exact same start and end times as #1?",
            "Which person held an affiliation to Elite (Comoros) starting and ending at the same dates as #1?",
            "Who had the same affiliation period to Elite (Comoros) as the timeframe identified in #1?"
        ]
    }}
]

**Example 8:**
Input: During Jüri Pihl Affiliation To Social Democratic Party, which organisation is Affiliation Toed by Sergion Sebastiani?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When was Jüri Pihl affiliated with the Social Democratic Party?",
            "What is the time period of Jüri Pihl's affiliation to the Social Democratic Party?",
            "At what time did Jüri Pihl hold an affiliation to the Social Democratic Party?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which organisation was Sergion Sebastiani affiliated with during #1?",
            "To which organisation did Sergion Sebastiani hold an affiliation during the period #1?",
            "What organisation had an affiliation by Sergion Sebastiani within the timeframe #1?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

icews_actor_complex = """# Role
You are an Advanced Logic Decomposition Engine. Your goal is to break down complex questions involving multiple entities (usually 3+), timeline intersections, rankings, or comparative durations into atomic sub-questions.

# Task
1.  **Analyze the Question**: Identify the entities and the specific temporal logic:
    * **Intersection/Simultaneity**: "at the same time", "during... during...".
    * **Allen Interval Logic**: "finishedby", "starts", "equal", "overlapped by".
    * **Sequence**: "after... after...", "before... before...".
    * **Ranking/Aggregation**: "ranking what based on start time", "total duration of A, B, and C".
2.  **Decompose**: Break the question into sequential steps. Generate simple retrieval questions to get the start/end dates for **each** person/entity mentioned.
3.  **Output Structure**: For each step, output a JSON object containing:
    * `idx`: The sequential index (starting from "1").
    * `variants`: A list of **exactly 3 distinct**, grammatically correct ways to phrase this sub-question.
4.  **Dependency & Slot Filling**: Use `#idx` (e.g., `#1`, `#2`) to refer to the **answer/result** of a previous sub-question.

# Constraints
* **Date Precision**: Do not change "beginning of time" or "end of time". If an explicit date is present, use "YYYY-MM-DD".
* **Entity Precision**: Preserve specific entity names exactly as they appear (e.g., "RLI Corporation").
* **Natural Phrasing**: Do not include technical format strings inside the `variants` text. Keep the questions conversational.

# Examples

**Example 1:**
Input: From when to when, Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction, at the same time, António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal), at the same time, Ricardo Arias Calderon Affiliation To Christian Democratic Party?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "From when to when was Mariama Sarr-Ceesay affiliated with the Alliance for Patriotic Reorientation and Construction?",
            "What is the time period of Mariama Sarr-Ceesay's affiliation to the Alliance for Patriotic Reorientation and Construction?",
            "When did Mariama Sarr-Ceesay hold an affiliation to the Alliance for Patriotic Reorientation and Construction?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "From when to when was António Manuel Mascarenhas Gomes Monteiro affiliated with the Government (Portugal)?",
            "What is the time period of António Manuel Mascarenhas Gomes Monteiro's affiliation to the Government (Portugal)?",
            "When did António Manuel Mascarenhas Gomes Monteiro hold an affiliation to the Government (Portugal)?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "From when to when was Ricardo Arias Calderon affiliated with the Christian Democratic Party?",
            "What is the time period of Ricardo Arias Calderon's affiliation to the Christian Democratic Party?",
            "When did Ricardo Arias Calderon hold an affiliation to the Christian Democratic Party?"
        ]
    }}
]

**Example 2:**
Input: Ricardo Arias Calderon Affiliation To which organisation, finishedby Oswaldo Álvarez Paz Affiliation To Popular Alliance, finishedby Dave Heineman Affiliation To Nebraska?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Oswaldo Álvarez Paz end his affiliation with the Popular Alliance?",
            "What is the end date of Oswaldo Álvarez Paz's affiliation to the Popular Alliance?",
            "At what time did Oswaldo Álvarez Paz cease being affiliated with the Popular Alliance?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "When did Dave Heineman end his affiliation with Nebraska?",
            "What is the end date of Dave Heineman's affiliation to Nebraska?",
            "At what time did Dave Heineman cease being affiliated with Nebraska?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "Which organisation was Ricardo Arias Calderon affiliated with that finished at the same time as #1 and #2?",
            "Identify the organisation whose affiliation with Ricardo Arias Calderon ended on the dates #1 and #2.",
            "What affiliation of Ricardo Arias Calderon concluded simultaneously with #1 and #2?"
        ]
    }}
]

**Example 3:**
Input: Who Raila Odinga National Development Party, starts RLI Corporation Affiliation To Consulting / Financial Services Business (Multi-National Corporations), before Artis Pabriks Affiliation To, Ministry of Defence?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did RLI Corporation start its affiliation with Consulting / Financial Services Business (Multi-National Corporations)?",
            "What is the start date of RLI Corporation's affiliation to Consulting / Financial Services Business?",
            "At what time did RLI Corporation begin being affiliated with Consulting / Financial Services Business?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "When did Artis Pabriks start his affiliation with the Ministry of Defence?",
            "What is the start date of Artis Pabriks's affiliation to the Ministry of Defence?",
            "At what time did Artis Pabriks join the Ministry of Defence?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "Who was affiliated with the National Development Party starting at the same time as #1 and before #2?",
            "Identify the person whose affiliation with the National Development Party began on date #1 and prior to date #2.",
            "Which entity started their affiliation to the National Development Party simultaneously with #1 and before the event #2?"
        ]
    }}
]

**Example 4:**
Input: Sicily Affiliation To which organisation, during Fernando Olivera Affiliation To Council of Ministers of Peru, during Wendell H. Ford Affiliation To United States Senate?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "What is the time period of Fernando Olivera's affiliation to the Council of Ministers of Peru?",
            "From when to when was Fernando Olivera affiliated with the Council of Ministers of Peru?",
            "When did Fernando Olivera hold an affiliation to the Council of Ministers of Peru?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "What is the time period of Wendell H. Ford's affiliation to the United States Senate?",
            "From when to when was Wendell H. Ford affiliated with the United States Senate?",
            "When did Wendell H. Ford hold an affiliation to the United States Senate?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "Which organisation was Sicily affiliated with during both #1 and #2?",
            "To which organisation did Sicily have an affiliation throughout the overlapping periods of #1 and #2?",
            "Identify the organisation affiliated with Sicily within the timeframe defined by #1 and #2."
        ]
    }}
]

**Example 5:**
Input: Nasim Hamir Affiliation To which organisation, equal Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia, finishedby Roselyne Bachelot Affiliation To Council of Ministers?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "From when to when was Pasqual Maragall i Mira affiliated with the Socialists' Party of Catalonia?",
            "What are the start and end dates of Pasqual Maragall i Mira's affiliation to the Socialists' Party of Catalonia?",
            "Identify the exact duration of Pasqual Maragall i Mira's affiliation to the Socialists' Party of Catalonia."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "When did Roselyne Bachelot end her affiliation with the Council of Ministers?",
            "What is the end date of Roselyne Bachelot's affiliation to the Council of Ministers?",
            "At what time did Roselyne Bachelot cease being affiliated with the Council of Ministers?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "Which organisation was Nasim Hamir affiliated with that had the equal duration as #1 and finished at #2?",
            "Identify the organisation whose affiliation with Nasim Hamir matched the start and end times of #1 and ended at #2.",
            "To which organisation did Nasim Hamir have an affiliation that was concurrent with #1 and concluded with #2?"
        ]
    }}
]

**Example 6:**
Input: Patricia de Lille Affiliation To which organisation, after Zainal Hazari Affiliation To Opposition Major Party (Out Of Government) (Bangladesh), after Mark Pryor Affiliation To Arkansas?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Zainal Hazari end his affiliation with the Opposition Major Party (Out Of Government) (Bangladesh)?",
            "What is the end date of Zainal Hazari's affiliation to the Opposition Major Party in Bangladesh?",
            "At what time did Zainal Hazari cease being affiliated with the Opposition Major Party (Bangladesh)?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "When did Mark Pryor end his affiliation with Arkansas?",
            "What is the end date of Mark Pryor's affiliation to Arkansas?",
            "At what time did Mark Pryor cease being affiliated with Arkansas?"
        ]
    }},
    {
        "subq_idx": 3,
        "variants": [
            "Which organisation was Patricia de Lille affiliated with after both #1 and #2?",
            "To which organisation did Patricia de Lille have an affiliation starting subsequent to #1 and #2?",
            "Identify the organisation affiliated with Patricia de Lille following the dates #1 and #2."
        ]
    }}
]

**Example 7:**
Input: Jaroslav Spisiak is ranking what based on the start time amony Jaroslav Spisiak Affiliation To Slovak Police, Michael David Chong Affiliation To Progressive Conservative Party of Canada and Graciela Fernández Meijide Affiliation To Ministry of Social Action?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Jaroslav Spisiak start his affiliation with the Slovak Police?",
            "What is the start date of Jaroslav Spisiak's affiliation to the Slovak Police?",
            "At what time did Jaroslav Spisiak begin his affiliation with the Slovak Police?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "When did Michael David Chong start his affiliation with the Progressive Conservative Party of Canada?",
            "What is the start date of Michael David Chong's affiliation to the Progressive Conservative Party of Canada?",
            "At what time did Michael David Chong begin his affiliation with the Progressive Conservative Party of Canada?"
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "When did Graciela Fernández Meijide start her affiliation with the Ministry of Social Action?",
            "What is the start date of Graciela Fernández Meijide's affiliation to the Ministry of Social Action?",
            "At what time did Graciela Fernández Meijide begin her affiliation with the Ministry of Social Action?"
        ]
    }}
]

**Example 8:**
Input: How long is the total duration of Mark Malloch Brown Affiliation To Secretary of State for Foreign and Commonwealth Affairs, N.B. Rao Affiliation To Government (India) and Thomas Remengesau Affiliation To Government (Palau)?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "What is the duration of Mark Malloch Brown's affiliation with the Secretary of State for Foreign and Commonwealth Affairs?",
            "For how long was Mark Malloch Brown affiliated to the Secretary of State for Foreign and Commonwealth Affairs?",
            "Calculate the length of time Mark Malloch Brown held an affiliation to the Secretary of State for Foreign and Commonwealth Affairs."
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "What is the duration of N.B. Rao's affiliation with the Government (India)?",
            "For how long was N.B. Rao affiliated to the Government (India)?",
            "Calculate the length of time N.B. Rao held an affiliation to the Government (India)."
        ]
    }},
    {{
        "subq_idx": 3,
        "variants": [
            "What is the duration of Thomas Remengesau's affiliation with the Government (Palau)?",
            "For how long was Thomas Remengesau affiliated to the Government (Palau)?",
            "Calculate the length of time Thomas Remengesau held an affiliation to the Government (Palau)."
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

ic_infer = """# Role
You are an expert Temporal Knowledge Graph Query Agent specialized in political and actor affiliation data. Your task is to answer complex questions based strictly on the provided "Relevant facts".

# Task Instructions
1.  **Analyze the Temporal Logic**: Determine how to connect the sub-questions based on the query type.
    * **Symbolic Dates**: Handle `"beginning of time"` (treat as $-\infty$) and `"end of time"` (treat as $+\infty$).
    * **Intersection ("at the same time")**: Find the overlap of intervals.
        * Overlap([StartA, EndA], [StartB, EndB]) = [max(StartA, StartB), min(EndA, EndB)].
    * **Union ("or")**: Merge intervals.
    * **Duration Comparison**: Calculate length. If one is finite and the other is "beginning to end of time", the latter is longer.

2.  **Filter & Match Facts**:
    * Match entities in the query to the specific facts provided in the sub-questions.
    * Discard facts that do not match the requested relationship or entity.

3.  **Formulate Output**:
    * Return a JSON object containing:
        * `reason`: A step-by-step logical derivation explaining how the facts lead to the answer.
        * `events`: The list of exact fact strings used. **CRITICAL**: If the question has $N$ sub-questions, you must select exactly one relevant fact per sub-question to form a complete reasoning chain.
        * `answers`: A list of entities or time ranges.

# Constraints
* **Strict Adherence to Facts**: Do not use outside knowledge.
* **Event Alignment**: The `events` list must correspond 1-to-1 with the sub-questions in the reasoning chain.
* **Output Format**: JSON only.

#Examples

**Example 1:**
**Raw question**: Who Affiliation To National Democratic Party from beginning of time to 2006-12-31?
**Subquestion 1**: Who had an Affiliation To the National Democratic Party from beginning of time to 2006-12-31?
**Relevant facts 1**:
Andrus Ansip Affiliation To Estonian Reform Party from 2004-11-21 to end of time
Mohamed Noor Affiliation To Opposition Major Party (Out Of Government) (Malaysia) from beginning of time to end of time
Osama al-Ghazali Harb Affiliation To National Democratic Party from beginning of time to 2006-12-31
Joseph Habineza Affiliation To Ministry of Sports and Culture from 2006-01-02 to 2011-01-02
**Output**:
{{
    "reason": "The question asks for a person whose affiliation with the National Democratic Party spans exactly from 'beginning of time' to '2006-12-31'. Examining the facts, Osama al-Ghazali Harb matches this specific start and end date perfectly.",
    "events": [
        "Osama al-Ghazali Harb Affiliation To National Democratic Party from beginning of time to 2006-12-31"
    ],
    "answers": ["Osama al-Ghazali Harb"]
}}

**Example 2:**
**Raw question**: At what point did Max Bradford cease his affiliation with the major governing party in New Zealand?
**Subquestion 1**: At what point in time did Max Bradford cease his affiliation with the major governing party in New Zealand?
**Relevant facts 1**:
Max Bradford Affiliation To Government Major Party (In Government) (New Zealand) from 1960-11-26 to 1972-12-08
Aliou Sow Affiliation To Ministry of Decentralisation and Local Government from 2009-12-03 to end of time
Khodayyir Abbas Affiliation To Ministry of Health from 2003-09-01 to 2004-06-27
Bhaskara Rao Affiliation To Government (India) from beginning of time to end of time
**Output**:
{{
    "reason": "The question asks for the cessation point (end date) of Max Bradford's affiliation. The relevant fact shows his affiliation was from 1960-11-26 to 1972-12-08. Therefore, he ceased his affiliation on 1972-12-08.",
    "events": [
        "Max Bradford Affiliation To Government Major Party (In Government) (New Zealand) from 1960-11-26 to 1972-12-08"
    ],
    "answers": ["1972-12-08"]
}}

**Example 3:**
**Raw question**: How long is the total duration of Atta Mohammed Nur Affiliation To Northern Alliance and Kennedy Sakeni Affiliation To Ministry of Home Affairs?
**Subquestion 1**: What was the duration of Atta Mohammed Nur's affiliation to the Northern Alliance?
**Relevant facts 1**:
Association Of Former International Civil Servants Affiliation To Development IGOs (Non-Governmental Organizations) from beginning of time to end of time
Atta Mohammed Nur Affiliation To Northern Alliance from 1988-01-01 to 2004-10-01
Jim Knight Affiliation To Labour Party from beginning of time to end of time
**Subquestion 2**: What was the duration of Kennedy Sakeni's affiliation to the Ministry of Home Affairs?
**Relevant facts 2**:
François Baroin Affiliation To Union for a Popular Movement from beginning of time to end of time
Kennedy Sakeni Affiliation To Ministry of Home Affairs from 2011-09-23 to 2012-07-10
José Endundo Bononge Affiliation To Cabinet (Democratic Republic of Congo) from 2008-10-26 to end of time
Stefano Rodotà Affiliation To Legal (Italy) from beginning of time to end of time
**Output**:
{{
    "reason": "We need to sum two durations. 1) Atta Mohammed Nur (1988-01-01 to 2004-10-01) is approx 16 years, 9 months. 2) Kennedy Sakeni (2011-09-23 to 2012-07-10) is approx 9 months, 17 days. Adding these intervals yields a total duration of roughly 17 years, 6 months, and 24 days.",
    "events": [
        "Atta Mohammed Nur Affiliation To Northern Alliance from 1988-01-01 to 2004-10-01",
        "Kennedy Sakeni Affiliation To Ministry of Home Affairs from 2011-09-23 to 2012-07-10"
    ],
    "answers": ["17 years, 6 months, 24 days, 0 hours, 0 minutes, 0 seconds"]
}}

**Example 4:**
**Raw question**: At the same time André Kimbuta Affiliation To People's Party for Reconstruction and Democracy, in which organisation Manila Times Affiliation To?
**Subquestion 1**: At what time did André Kimbuta hold an affiliation to the People's Party for Reconstruction and Democracy?
**Relevant facts 1**:
André Kimbuta Affiliation To People's Party for Reconstruction and Democracy from beginning of time to end of time
Malcolm Bligh Turnbull Affiliation To Lower House (Australia) from 2004-10-09 to end of time
Lily Pérez Affiliation To Chamber of Deputies of Chile from 1998-03-11 to 2006-03-10
**Subquestion 2**: Which organisation was the Manila Times affiliated with during the time #1?
**Relevant facts 2**:
Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time
Khodayyir Abbas Affiliation To Ministry of Health from 2003-09-01 to 2004-06-27
Moussa Koussa Affiliation To Exiles (Libya) from 2011-03-31 to end of time
**Output**:
{{
    "reason": "André Kimbuta's affiliation spans from 'beginning of time' to 'end of time'. We need to find the Manila Times' affiliation during this overlap. The fact shows Manila Times was affiliated to 'Print News (Philippines)' also from 'beginning of time' to 'end of time'. Since the intervals completely overlap, 'Print News (Philippines)' is the correct organization.",
    "events": [
        "Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time",
        "André Kimbuta Affiliation To People's Party for Reconstruction and Democracy from beginning of time to end of time"
    ],
    "answers": ["Print News (Philippines)"]
}}

**Example 5:**
**Raw question**: Is the duration of José de Gregorio Affiliation To Central Bank of Chile shorter the duration of Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco)?
**Subquestion 1**: What is the duration of José de Gregorio's affiliation with the Central Bank of Chile?
**Relevant facts 1**:
José de Gregorio Affiliation To Central Bank of Chile from 2003-12-06 to 2007-12-06
Einars Repse Affiliation To Ministry of Finance from 2009-03-12 to 2010-11-03
Suleimane Djassi Affiliation To Ministry of Tourism from 2003-10-02 to 2004-05-11
Norman Chibamba Affiliation To Ministry of Community Development and Social Services from 2004-01-02 to 2005-01-01
**Subquestion 2**: What is the duration of Hightech Payment Systems' affiliation with Consulting / Financial Services Business (Morocco)?
**Relevant facts 2**:
Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco) from beginning of time to end of time
Douglas Devananda Affiliation To Unidentified Forces (Sri Lanka) from beginning of time to end of time
Nayef bin Abdulaziz al-Saud Affiliation To Elite (Saudi Arabia) from beginning of time to end of time
**Output**:
{{
    "reason": "José de Gregorio's duration is exactly 4 years (2003-12-06 to 2007-12-06). Hightech Payment Systems' duration is 'beginning of time to end of time', which represents an infinite or maximal duration. 4 years is strictly shorter than the infinite duration.",
    "events": [
        "José de Gregorio Affiliation To Central Bank of Chile from 2003-12-06 to 2007-12-06",
        "Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco) from beginning of time to end of time"
    ],
    "answers": ["shorter"]
}}

**Example 6:**
**Raw question**: From when to when, Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction, at the same time, António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal), at the same time, Ricardo Arias Calderon Affiliation To Christian Democratic Party?
**Subquestion 1**: When did Mariama Sarr-Ceesay hold an affiliation to the Alliance for Patriotic Reorientation and Construction?
**Relevant facts 1**:
Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction from beginning of time to end of time
Judge Safair Affiliation To Judicial (India) from beginning of time to end of time
Walfrido Silvino dos Mares Guia Neto Affiliation To Brazilian Labour Party from beginning of time to end of time
**Subquestion 2**: What is the time period of António Manuel Mascarenhas Gomes Monteiro's affiliation to the Government (Portugal)?
**Relevant facts 2**:
António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal) from 1991-03-22 to 2001-03-22
Attorney General Ruddock Affiliation To Opposition Major Party (Out Of Government) (Australia) from beginning of time to 1939-04-25
Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time
**Subquestion 3**: When did Ricardo Arias Calderon hold an affiliation to the Christian Democratic Party?
**Relevant facts 3**:
Ricardo Arias Calderon Affiliation To Christian Democratic Party from beginning of time to end of time
Romárico Arroyo Affiliation To Cabinet (Mexico) from 1998-01-05 to 2000-11-30
Basil Pesambili Mramba Affiliation To Party of the Revolution from beginning of time to end of time
**Output**:
{{
    "reason": "We need the intersection of three time intervals: 1) Mariama: All Time; 2) António: 1991-03-22 to 2001-03-22; 3) Ricardo: All Time. The intersection of [All Time] AND [1991-2001] AND [All Time] is the most restrictive interval, which is [1991-03-22 to 2001-03-22].",
    "events": [
        "Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction from beginning of time to end of time",
        "António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal) from 1991-03-22 to 2001-03-22".
        "Ricardo Arias Calderon Affiliation To Christian Democratic Party from beginning of time to end of time"
    ],
    "answers": ["(1991-03-22, 2001-03-22)"]
}}

**Example 7:**
**Raw question**: Nasim Hamir Affiliation To which organisation, equal Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia, finishedby Roselyne Bachelot Affiliation To Council of Ministers?
**Subquestion 1**: From when to when was Pasqual Maragall i Mira affiliated with the Socialists' Party of Catalonia?
**Relevant facts 1**:
Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia from beginning of time to end of time
Shoeb Ali Affiliation To Police (India) from beginning of time to end of time
Einars Repse Affiliation To Ministry of Finance from 2009-03-12 to 2010-11-03
**Subquestion 2**: When did Roselyne Bachelot end her affiliation with the Council of Ministers?
**Relevant facts 2**:
Roselyne Bachelot Affiliation To Council of Ministers from 2007-05-18 to end of time
Jigme Wangchuk Affiliation To Executive Office (Bhutan) from 1926-08-21 to 1952-03-30
N.B. Rao Affiliation To Government (India) from beginning of time to end of time
**Subquestion 3**: Which organisation was Nasim Hamir affiliated with that had the equal duration as #1 and finished at #2?
**Relevant facts 3**:
Nasim Hamir Affiliation To Movement for Multi-Party Democracy from beginning of time to end of time
Botswana Mine Workers Union Affiliation To Botswana Federation of Trade Unions from beginning of time to end of time
Jesusa Obono Engono Affiliation To Council of Ministers from 2004-06-14 to 2006-08-14
**Output**:
{{
    "reason": "We need an affiliation for Nasim Hamir that is 'equal' to Pasqual's (beginning to end of time) AND 'finishedby' Roselyne's (end of time). Pasqual's interval is [beginning, end]. Roselyne's ends at [end]. Nasim Hamir's affiliation to 'Movement for Multi-Party Democracy' is [beginning, end]. This matches Pasqual's duration exactly (equal) and shares the same end time as Roselyne (finishedby).",
    "events": [
        "Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia from beginning of time to end of time",
        "Roselyne Bachelot Affiliation To Council of Ministers from 2007-05-18 to end of time",
        "Nasim Hamir Affiliation To Movement for Multi-Party Democracy from beginning of time to end of time"
    ],
    "answers": ["Movement for Multi-Party Democracy"]
}}

"""

ic_fallback = """# Role
You are an expert Temporal Knowledge Graph Query Agent. Your task is to answer a complex question based strictly on the provided "Relevant facts".

# Task Instructions
1.  **Analyze the Question**: Determine the temporal logic required.
    - **Intersection**: "at the same time" (Find overlap).
    - **Union**: "or" (Merge time intervals).
    - **Sequence**: "before", "after", "then" (Compare timestamps).
    - **Duration**: "from when to when", "how long" (Calculate start and end or length).
    - **Logic**: "equal", "finishedby", "starts" (Allen Interval Logic).
2.  **Filter Facts**: The provided facts come from the question. Identify which facts correspond to the entities in the user's query. Discard irrelevant facts.
3.  **Temporal Reasoning**: Perform the necessary calculations (min, max, comparison) on the dates.
    - Handle "beginning of time" as negative infinity and "end of time" as positive infinity.
4.  **Formulate Output**:
    - Return a JSON object with:
        - `reason`: A step-by-step derivation of the answer.
        - `events`: A list of the specific fact strings from relevant facts used to derive the answer.
        - `answers`: A list containing the final entities or normalized dates (YYYY-MM-DD).

# Constraints
- **Strict Adherence to Facts**: Do not use outside knowledge. If the facts do not support an answer, return [].
- **Time Format**: All dates must be normalized to YYYY-MM-DD.
- **Intersection Logic**: Overlap = [max(StartA, StartB), min(EndA, EndB)]. Condition: Start <= End.
- **Union Logic**: If intervals overlap or touch, merge them: [min(StartA, StartB), max(EndA, EndB)].
- **Event Alignment (CRITICAL)**: If the question involves $N$ logic steps or entities, the `events` list must represent the complete reasoning chain.
- **Output Format**: JSON only.

#Examples

**Example 1:**
**Relevant facts**:
Andrus Ansip Affiliation To Estonian Reform Party from 2004-11-21 to end of time
Mohamed Noor Affiliation To Opposition Major Party (Out Of Government) (Malaysia) from beginning of time to end of time
Osama al-Ghazali Harb Affiliation To National Democratic Party from beginning of time to 2006-12-31
Joseph Habineza Affiliation To Ministry of Sports and Culture from 2006-01-02 to 2011-01-02
**Question**: Who Affiliation To National Democratic Party from beginning of time to 2006-12-31?
**Output**:
{{
    "reason": "The question asks for a person whose affiliation with the National Democratic Party strictly spans from 'beginning of time' to '2006-12-31'. Scanning the facts, Osama al-Ghazali Harb's affiliation matches these start and end points exactly.",
    "events": [
        "Osama al-Ghazali Harb Affiliation To National Democratic Party from beginning of time to 2006-12-31"
    ],
    "answers": ["Osama al-Ghazali Harb"]
}}

**Example 2:**
**Relevant facts**:
Max Bradford Affiliation To Government Major Party (In Government) (New Zealand) from 1960-11-26 to 1972-12-08
Aliou Sow Affiliation To Ministry of Decentralisation and Local Government from 2009-12-03 to end of time
Khodayyir Abbas Affiliation To Ministry of Health from 2003-09-01 to 2004-06-27
Bhaskara Rao Affiliation To Government (India) from beginning of time to end of time
**Question**: At what point did Max Bradford cease his affiliation with the major governing party in New Zealand?
**Output**:
{{
    "reason": "The question asks for the end date ('cease point') of Max Bradford's affiliation. The relevant fact states his affiliation was from 1960-11-26 to 1972-12-08. Therefore, the cessation date is 1972-12-08.",
    "events": [
        "Max Bradford Affiliation To Government Major Party (In Government) (New Zealand) from 1960-11-26 to 1972-12-08"
    ],
    "answers": ["1972-12-08"]
}}

**Example 3:**
**Relevant facts**:
Association Of Former International Civil Servants Affiliation To Development IGOs (Non-Governmental Organizations) from beginning of time to end of time
Atta Mohammed Nur Affiliation To Northern Alliance from 1988-01-01 to 2004-10-01
Jim Knight Affiliation To Labour Party from beginning of time to end of time
François Baroin Affiliation To Union for a Popular Movement from beginning of time to end of time
Kennedy Sakeni Affiliation To Ministry of Home Affairs from 2011-09-23 to 2012-07-10
José Endundo Bononge Affiliation To Cabinet (Democratic Republic of Congo) from 2008-10-26 to end of time
Stefano Rodotà Affiliation To Legal (Italy) from beginning of time to end of time
**Question**: How long is the total duration of Atta Mohammed Nur Affiliation To Northern Alliance and Kennedy Sakeni Affiliation To Ministry of Home Affairs?
**Output**:
{{
    "reason": "We calculate two durations: 1) Atta Mohammed Nur (1988-01-01 to 2004-10-01) is approx 16 years, 9 months. 2) Kennedy Sakeni (2011-09-23 to 2012-07-10) is approx 9 months, 17 days. Summing these intervals gives a total duration of roughly 17 years, 6 months, and 24 days.",
    "events": [
        "Atta Mohammed Nur Affiliation To Northern Alliance from 1988-01-01 to 2004-10-01",
        "Kennedy Sakeni Affiliation To Ministry of Home Affairs from 2011-09-23 to 2012-07-10"
    ],
    "answers": ["17 years, 6 months, 24 days, 0 hours, 0 minutes, 0 seconds"]
}}

**Example 4:**
**Relevant facts**:
André Kimbuta Affiliation To People's Party for Reconstruction and Democracy from beginning of time to end of time
Malcolm Bligh Turnbull Affiliation To Lower House (Australia) from 2004-10-09 to end of time
Lily Pérez Affiliation To Chamber of Deputies of Chile from 1998-03-11 to 2006-03-10
Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time
Khodayyir Abbas Affiliation To Ministry of Health from 2003-09-01 to 2004-06-27
Moussa Koussa Affiliation To Exiles (Libya) from 2011-03-31 to end of time
**Question**: At the same time André Kimbuta Affiliation To People's Party for Reconstruction and Democracy, in which organisation Manila Times Affiliation To?
**Output**:
{{
    "reason": "André Kimbuta's affiliation is 'beginning of time' to 'end of time'. We look for the Manila Times' affiliation that overlaps with this. Manila Times was affiliated to 'Print News (Philippines)' also from 'beginning of time' to 'end of time'. Since the intervals fully overlap, this is the correct organization.",
    "events": [
        "Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time",
        "André Kimbuta Affiliation To People's Party for Reconstruction and Democracy from beginning of time to end of time"
    ],
    "answers": ["Print News (Philippines)"]
}}

**Example 5:**
**Relevant facts**:
José de Gregorio Affiliation To Central Bank of Chile from 2003-12-06 to 2007-12-06
Einars Repse Affiliation To Ministry of Finance from 2009-03-12 to 2010-11-03
Suleimane Djassi Affiliation To Ministry of Tourism from 2003-10-02 to 2004-05-11
Norman Chibamba Affiliation To Ministry of Community Development and Social Services from 2004-01-02 to 2005-01-01
Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco) from beginning of time to end of time
Douglas Devananda Affiliation To Unidentified Forces (Sri Lanka) from beginning of time to end of time
Nayef bin Abdulaziz al-Saud Affiliation To Elite (Saudi Arabia) from beginning of time to end of time
**Question**: Is the duration of José de Gregorio Affiliation To Central Bank of Chile shorter the duration of Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco)?
**Output**:
{{
    "reason": "José de Gregorio's duration is exactly 4 years (2003-2007). Hightech Payment Systems' duration spans from 'beginning of time' to 'end of time', effectively infinite. 4 years is strictly shorter than an infinite duration.",
    "events": [
        "José de Gregorio Affiliation To Central Bank of Chile from 2003-12-06 to 2007-12-06",
        "Hightech Payment Systems Affiliation To Consulting / Financial Services Business (Morocco) from beginning of time to end of time"
    ],
    "answers": ["shorter"]
}}

**Example 6:**
**Relevant facts**:
Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction from beginning of time to end of time
Judge Safair Affiliation To Judicial (India) from beginning of time to end of time
Walfrido Silvino dos Mares Guia Neto Affiliation To Brazilian Labour Party from beginning of time to end of time
António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal) from 1991-03-22 to 2001-03-22
Attorney General Ruddock Affiliation To Opposition Major Party (Out Of Government) (Australia) from beginning of time to 1939-04-25
Manila Times Affiliation To Print News (Philippines) from beginning of time to end of time
Ricardo Arias Calderon Affiliation To Christian Democratic Party from beginning of time to end of time
Romárico Arroyo Affiliation To Cabinet (Mexico) from 1998-01-05 to 2000-11-30
Basil Pesambili Mramba Affiliation To Party of the Revolution from beginning of time to end of time
**Question**: From when to when, Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction, at the same time, António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal), at the same time, Ricardo Arias Calderon Affiliation To Christian Democratic Party?
**Output**:
{{
    "reason": "The question requires the intersection of three affiliations. Mariama and Ricardo both have affiliations from 'beginning of time' to 'end of time'. António's affiliation is from 1991-03-22 to 2001-03-22. The intersection of [All Time] AND [All Time] AND [1991-2001] is simply [1991-03-22 to 2001-03-22].",
    "events": [
        "Mariama Sarr-Ceesay Affiliation To Alliance for Patriotic Reorientation and Construction from beginning of time to end of time",
        "António Manuel Mascarenhas Gomes Monteiro Affiliation To Government (Portugal) from 1991-03-22 to 2001-03-22".
        "Ricardo Arias Calderon Affiliation To Christian Democratic Party from beginning of time to end of time"
    ],
    "answers": ["(1991-03-22, 2001-03-22)"]
}}

**Example 7:**
**Relevant facts**:
Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia from beginning of time to end of time
Shoeb Ali Affiliation To Police (India) from beginning of time to end of time
Einars Repse Affiliation To Ministry of Finance from 2009-03-12 to 2010-11-03
Roselyne Bachelot Affiliation To Council of Ministers from 2007-05-18 to end of time
Jigme Wangchuk Affiliation To Executive Office (Bhutan) from 1926-08-21 to 1952-03-30
N.B. Rao Affiliation To Government (India) from beginning of time to end of time
Nasim Hamir Affiliation To Movement for Multi-Party Democracy from beginning of time to end of time
Botswana Mine Workers Union Affiliation To Botswana Federation of Trade Unions from beginning of time to end of time
Jesusa Obono Engono Affiliation To Council of Ministers from 2004-06-14 to 2006-08-14
**Question**: Nasim Hamir Affiliation To which organisation, equal Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia, finishedby Roselyne Bachelot Affiliation To Council of Ministers?
**Output**:
{{
    "reason": "We need an affiliation for Nasim Hamir that is 'equal' to Pasqual's (starts beginning of time, ends end of time) AND 'finishedby' Roselyne's (ends end of time). Nasim Hamir's affiliation to 'Movement for Multi-Party Democracy' spans from beginning to end of time. This satisfies 'equal' with Pasqual and shares the 'end of time' finish with Roselyne.",
    "events": [
        "Pasqual Maragall i Mira Affiliation To Socialists' Party of Catalonia from beginning of time to end of time",
        "Roselyne Bachelot Affiliation To Council of Ministers from 2007-05-18 to end of time",
        "Nasim Hamir Affiliation To Movement for Multi-Party Democracy from beginning of time to end of time"
    ],
    "answers": ["Movement for Multi-Party Democracy"]
}}

"""