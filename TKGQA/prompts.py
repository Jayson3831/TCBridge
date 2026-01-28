after_first = """# Role
You are a sophisticated Question Decomposition Engine. Your task is to break down complex "after_first" type questions into logical sub-questions that build upon each other.

# Task Definition
You will receive a list of questions that follow the pattern: "After [Event X], who/what was the first to do [Action Y]?" (or "Who was the first to do [Action Y] after [Event X]?")

For each question, you must generate a JSON object containing the decomposition. The decomposition must follow these strict rules:

1.  **Decomposition Logic**:
    * **Sub-question 1 (idx: 1)**: Ask for the specific time, founding date, or occurrence date of [Event X].
    * **Sub-question 2 (idx: 2)**: Ask for the entity that performed [Action Y] first *after* the time determined in Sub-question 1.
2.  **Placeholder Requirement**:
    * In **Sub-question 2**, you must NOT assume the date. Instead, you MUST use the placeholder `#1` to refer to the temporal answer from Sub-question 1.
3.  **Variant Generation**:
    * For each sub-question, provide exactly **3 distinct variants**.
    * The variants must use different phrasing or sentence structures but **must strictly preserve the original semantic meaning**.
4.  **Entity Type Consistency (CRITICAL)**:
    * You must strictly preserve the interrogative pronoun based on the entity type requested in the original question.
    * If the original question asks for a person, use **"Who"**, **"Whom"**, or **"Whose"**.
    * If the original question asks for a country/nation, use **"Which country"** or **"Which nation"**. Do NOT use "Who" for countries.
    * If the original question asks for an organization or object, use **"Which organization"**, **"Which company"**, or **"What"** appropriately.
    * **Do not generalize specific entity types into generic pronouns (e.g., do not change "Which country" to "Who").**
    * **NEVER use vague terms like "which entity" or "which party".**
5.  **Output Format**:
    * Output strictly valid JSON.
    * Do not include markdown code blocks (```json) or introductory text. Just the raw JSON data.

# Examples

**Example 1:**
Input: After the International Monetary Fund, with which country did Japan first express its intention to negotiate?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Japan express its intention to negotiate with the International Monetary Fund?",
            "At what time did Japan express its intention to negotiate with the International Monetary Fund?",
            "What is the date when Japan expressed its intention to negotiate with the International Monetary Fund?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "With which country did Japan express its intention to negotiate first after #1?",
            "After #1, with which country did Japan first express its intention to negotiate?",
            "Which country was the first that Japan expressed its intention to negotiate with after #1?"
        ]
    }}
]

**Example 2:**
Input: Who was the first to visit France after the Royal Administration of Wallis and Futuna?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did the Royal Administration of Wallis and Futuna visit France?",
            "At what time did the Royal Administration of Wallis and Futuna visit France?",
            "What is the date when the Royal Administration of Wallis and Futuna visited France?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was the first to visit France after #1?",
            "After #1, who was the first to visit France?",
            "Who visited France first after #1?"
        ]
    }}
]

**Example 3:**
Input: After the Navy of the United States, which country did Iran accuse first?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Iran accuse the Navy of the United States?",
            "At what time did Iran accuse the Navy of the United States?",
            "What is the date when Iran accused the Navy of the United States?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country did Iran accuse first after #1?",
            "After #1, which country did Iran accuse first?",
            "Which country was the first accused by Iran after #1?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the format above:

"""

before_last = """# Role
You are an expert Logical Question Decomposition Engine. Your goal is to break down complex "before_last" temporal reasoning questions into structured sub-questions with semantic variants, outputting the result in strict JSON format.

# Task Instructions
You will receive questions in the format: "Before [Event X], who/what was the last to do [Action Y]?" (or "Who was the last to do [Action Y] before [Event X]?")

For each input question, you must generate a JSON object following these specific rules:

1.  **Decomposition Logic**:
    * **Sub-question 1 (idx: 1)**: Ask for the specific time or occurrence date of [Event X] (the event acting as the temporal boundary).
    * **Sub-question 2 (idx: 2)**: Ask for the entity that performed [Action Y] **last** *before* the time found in step 1.
2.  **Placeholder Requirement**:
    * In **Sub-question 2**, you must NOT assume the date. Instead, you MUST use the placeholder `#1` to refer to the temporal answer from Sub-question 1.
3.  **Variant Generation**:
    * For each sub-question, provide exactly **3 distinct variants**.
    * Variants must have different sentence structures or phrasings but must preserve the **exact same semantic meaning**.
4.  **Entity Type Consistency (CRITICAL)**:
    * You must strictly preserve the interrogative pronoun based on the entity type requested in the original question.
    * If the original question asks for a person, use **"Who"**, **"Whom"**, or **"Whose"**.
    * If the original question asks for a country/nation, use **"Which country"** or **"Which nation"**. Do NOT use "Who" for countries.
    * If the original question asks for an organization or object, use **"Which organization"**, **"Which company"**, or **"What"** appropriately.
    * **Do not generalize specific entity types into generic pronouns (e.g., do not change "Which country" to "Who").**
    * **NEVER use vague terms like "which entity" or "which party".**
5.  **Output Format**:
    * Output strictly valid JSON.
    * Do not include markdown code blocks (```json) or introductory text. Just the raw JSON data.

# Examples

**Example 1:**
Input: Which country was the last to express optimism about the leader of Ukraine, before Iran?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Iran express optimism about the leader of Ukraine?",
            "At what time did Iran express optimism about the leader of Ukraine?",
            "What is the date when Iran expressed optimism about the leader of Ukraine?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country was the last to express optimism about the leader of Ukraine before #1?",
            "Before #1, which country was the last to express optimism about the leader of Ukraine?",
            "Which nation expressed optimism about the leader of Ukraine last before #1?"
        ]
    }}
]

**Example 2:**
Input: Before France, who last wished to meet with Nuri al-Maliki?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did France wish to meet with Nuri al-Maliki?",
            "At what time did France wish to meet with Nuri al-Maliki?",
            "What is the date when France wished to meet with Nuri al-Maliki?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who last wished to meet with Nuri al-Maliki before #1?",
            "Before #1, who last wished to meet with Nuri al-Maliki?",
            "Who was the last to wish to meet with Nuri al-Maliki before #1?"
        ]
    }}
]

**Example 3:**
Input: Who was the last country to be attacked with small arms and light weapons by the Brazilian military before Colombia?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When was Colombia attacked with small arms and light weapons by the Brazilian military?",
            "At what time was Colombia attacked with small arms and light weapons by the Brazilian military?",
            "What is the date when Colombia was attacked with small arms and light weapons by the Brazilian military?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country was the last to be attacked with small arms and light weapons by the Brazilian military before #1?",
            "Before #1, which country was the last to be attacked with small arms and light weapons by the Brazilian military?",
            "Which nation was attacked with small arms and light weapons by the Brazilian military last before #1?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the format above:

"""

equal_multi = """# Role
You are an expert Logical Question Decomposition Engine. Your goal is to process "equal_multi" type questions. These questions involve finding an entity based on a shared timestamp (same year, month, day) or a specific time constraint combined with ranking (first/last).

# Task Instructions
You will receive questions that fall into two distinct subtypes. You must identify the subtype and apply the corresponding decomposition logic.

### Subtype A: Explicit Time (Questions with specific years/dates)
* **Pattern**: The question explicitly mentions a year (e.g., "in 2005") or date, often combined with "first" or "last".
* **Logic**: No complex decomposition is needed. You only need to standardize the phrasing.
* **Output format**:
    * **Sub-question 1 (idx: 1)**: The original question itself, ensuring the time information (e.g., "in 2005") and ranking keywords ("first", "last") are preserved.
    * **Variants**: Provide 3 variants of the full question.

### Subtype B: Relative Time (Questions comparing two events)
* **Pattern**: The question lacks a specific year but uses phrases like "in the same year as", "in the same month as", "on the same day of", implying a dependency on another event.
* **Logic**:
    * **Sub-question 1 (idx: 1)**: Ask for the time/date of the **reference event** mentioned in the comparison (the "as [Entity/Event]" part).
    * **Sub-question 2 (idx: 2)**: Ask for the target entity performing the action at the **same time** as the reference event.
    * **Placeholder**: Sub-question 2 MUST use `#1` to represent the time derived from Sub-question 1.
* **Output format**:
    * Generate two distinct sub-questions (idx: 1 and idx: 2) with 3 variants each.

# General Rules
1.  **Variants**: For every sub-question, provide exactly **3 distinct variants** with the same semantic meaning.
2.  **Time Normalization**: Normalize them to the international standard ISO 8601 format: YYYY-MM-DD for specific dates, YYYY-MM for year-month precision, and YYYY for year-only precision.
3.  **Entity Type Consistency (CRITICAL)**:
    * You must strictly preserve the interrogative pronoun based on the entity type requested in the original question.
    * If the original question asks for a person, use **"Who"**, **"Whom"**, or **"Whose"**.
    * If the original question asks for a country/nation, use **"Which country"** or **"Which nation"**. Do NOT use "Who" for countries.
    * If the original question asks for an organization or object, use **"Which organization"**, **"Which company"**, or **"What"** appropriately.
    * **Do not generalize specific entity types into generic pronouns (e.g., do not change "Which country" to "Who").**
    * **NEVER use vague terms like "which entity" or "which party".**
4.  **Output Format**: Output strict JSON only. No markdown formatting or extra text.

# Examples

**Example 1 (Subtype A - Explicit Time / First):**
Input: Who was the first to request a meeting with Togo in 2005?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who was the first to request a meeting with Togo in 2005?",
            "In 2005, who was the first to ask for a meeting with Togo?",
            "Who submitted the first request to meet with Togo during the year 2005?"
        ]
    }}
]

**Example 2 (Subtype A - Explicit Time / Last):**
Input: Which country last praised Iran in 2009?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Which country last praised Iran in 2009?",
            "In 2009, which country was the last to praise Iran?",
            "Which nation was the last to praise Iran in the year 2009?"
        ]
    }}
]

**Example 3 (Subtype B - Relative Time / Same Year):**
Input: Who hosted the visit of Abdelkader Messahel to Mauritania in the same year?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Abdelkader Messahel visit Mauritania?",
            "In which year did Abdelkader Messahel visit Mauritania?",
            "What is the date of Abdelkader Messahel's visit to Mauritania?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who hosted the visit of Abdelkader Messahel to Mauritania in #1?",
            "In the year #1, who hosted the visit of Abdelkader Messahel to Mauritania?",
            "Who was the host for Abdelkader Messahel's visit to Mauritania in #1?"
        ]
    }}
]

**Example 4 (Subtype B - Relative Time / Same Month):**
Input: Who praised Iran in the same month as Nacer Mehal?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Nacer Mehal praise Iran?",
            "In which month did Nacer Mehal praise Iran?",
            "What is the date when Nacer Mehal praised Iran?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who praised Iran in the same month as #1?",
            "In the month of #1, who praised Iran?",
            "Who offered praise to Iran in #1?"
        ]
    }}
]
    
**Example 5 (Subtype B - Relative Time / Same Day):**
Input: Which country did the envoy of Sudan want to meet on the same day of Qatar?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did the envoy of Sudan want to meet Qatar?",
            "On which day did the envoy of Sudan want to meet Qatar?",
            "What is the date when the envoy of Sudan wanted to meet Qatar?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country did the envoy of Sudan want to meet on #1?",
            "On the day #1, which country did the envoy of Sudan want to meet?",
            "Which nation did the envoy of Sudan want to meet on #1?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above (identify if Subtype A or B automatically):

"""

before_after = """# Role
You are an expert Logical Question Decomposition Engine. Your goal is to process "before_after" type questions. These questions ask for entities that performed an action before or after a specific temporal anchor.

# Task Instructions
You will receive questions that fall into two distinct subtypes based on the nature of the temporal anchor. You must identify the subtype and apply the corresponding decomposition logic.

### Subtype A: Event-based Anchor (Relative Time)
* **Pattern**: The question compares the target action to another event (e.g., "After Japan...", "Before the citizens of State Actor did...").
* **Logic**:
    * **Sub-question 1 (idx: 1)**: Ask for the timestamp or occurrence date of the **anchor event**.
    * **Sub-question 2 (idx: 2)**: Ask for the target entity performing the action *before* or *after* the time derived from Sub-question 1.
    * **Placeholder**: Sub-question 2 MUST use `#1` to represent the time derived from Sub-question 1.
* **Output format**: Generate two distinct sub-questions (idx: 1 and idx: 2) with 3 variants each.

### Subtype B: Explicit Time Anchor
* **Pattern**: The question explicitly mentions a specific date or year (e.g., "after April 2011", "before 15 January 2008").
* **Logic**: No complex decomposition is needed because the time is already known.
* **Output format**:
    * **Sub-question 1 (idx: 1)**: The original question itself, ensuring the explicit date and the "before/after" logic are preserved.
    * **Variants**: Provide 3 variants of the full question.

# General Rules
1.  **Variants**: For every sub-question, provide exactly **3 distinct variants** with the same semantic meaning.
2.  **Time Normalization**: Normalize them to the international standard ISO 8601 format: YYYY-MM-DD for specific dates, YYYY-MM for year-month precision, and YYYY for year-only precision.
3.  **Entity Type Consistency (CRITICAL)**:
    * You must strictly preserve the interrogative pronoun based on the entity type requested in the original question.
    * If the original question asks for a person, use **"Who"**, **"Whom"**, or **"Whose"**.
    * If the original question asks for a country/nation, use **"Which country"** or **"Which nation"**. Do NOT use "Who" for countries.
    * If the original question asks for an organization or object, use **"Which organization"**, **"Which company"**, or **"What"** appropriately.
    * **Do not generalize specific entity types into generic pronouns (e.g., do not change "Which country" to "Who").**
    * **NEVER use vague terms like "which entity" or "which party".**
4.  **Output Format**: Output strict JSON only. No markdown formatting or extra text.

# Examples

**Example 1 (Subtype A - Relative / Before):**
Input: Who rejected Iran before the citizens of State Actor did?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did the citizens of State Actor reject Iran?",
            "What is the date when the citizens of State Actor rejected Iran?",
            "At what time did the citizens of State Actor reject Iran?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Before #1, who rejected Iran?",
            "Who rejected Iran prior to #1?",
            "Who rejected Iran earlier than #1?"
        ]
    }},
]

**Example 2 (Subtype A - Relative / After):**
Input: After Japan, who made South Korea suffer from conventional military forces?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Japan make South Korea suffer from conventional military forces?",
            "What is the date when Japan made South Korea suffer from conventional military forces?",
            "At what time did Japan make South Korea suffer from conventional military forces?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who made South Korea suffer from conventional military forces after #1?",
            "After #1, who made South Korea suffer from conventional military forces?",
            "Who attacked South Korea with conventional forces subsequent to #1?"
        ]
    }},
]

**Example 3 (Subtype B - Explicit Time / After):**
Input: Which country did Qatar appeal to after April 2011?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Which country did Qatar appeal to after 2011-04?",
            "After 2011-04, to which nation did Qatar make an appeal?",
            "After 2011-04, which country received an appeal from Qatar?"
        ]
    }},
]

**Example 4 (Subtype B - Explicit Time / Before):**
Input: Before 14 October 2015, who made Burundi suffer from conventional military forces?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who made Burundi suffer from conventional military forces before 2015-10-14?",
            "Who subjected Burundi to conventional military forces before 2015-10-14?",
            "Who used conventional military forces against Burundi before 2015-10-14?"
        ]
    }}
]

**Example 5 (Subtype B - Explicit Time / Before):**
Input: With which country did Qatar sign formal agreements before 15 January 2008?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "With which country did Qatar sign formal agreements before 2008-01-15?",
            "Which countries signed formal agreements with Qatar before 2008-01-15?",
            "Prior to 2008-01-15, with which nation did Qatar sign formal agreements?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above (identify if Subtype A or B automatically):

"""

first_last = """# Role
You are an expert Logical Question Decomposition Engine. Your goal is to process "first_last" type questions. These questions ask for the specific timestamp of the first or last occurrence of a single event.

# Task Instructions
You will receive questions that ask "When did [Entity] do [Action] for the first/last time?".

Since these questions refer to a single event without external dependencies, **no multi-step decomposition is needed**. Your task is to:

1.  **Single Step Processing**: Create a single sub-question object (idx: 1).
2.  **Variant Generation**: Provide exactly **3 distinct variants** of the original question.
3.  **Semantic Preservation**: Ensure the variants strictly preserve the temporal modifier ("first time", "last time", "initially", "most recently").

# General Rules
1.  **Variants**: For the single sub-question, provide exactly **3 distinct variants** with the same semantic meaning.
2.  **Entity Type Consistency (CRITICAL)**:
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
3.  **Output Format**: Output strict JSON only. No markdown formatting or extra text.

# Examples

**Example 1:**
Input: When did Iran praise South Africa for the first time?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Iran praise South Africa for the first time?",
            "At what time did Iran first praise South Africa?",
            "On what date did Iran initially praise South Africa?"
        ]
    }}
]

**Example 2:**
Input: When was the last time Hashim Thaçi spoke optimistically about Japan?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When was the last time Hashim Thaçi spoke optimistically about Japan?",
            "When did Hashim Thaçi most recently express optimism about Japan?",
            "At what time did Hashim Thaçi last voice confidence in Japan?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

equal = """# Role
You are an expert Logical Question Decomposition Engine. Your goal is to process "equal" type questions. These are direct lookup questions that map a specific time to an event/entity, or an event to a specific time.

# Task Instructions
You will receive questions that fall into two simple categories. Since these are atomic queries without dependencies, **no multi-step decomposition is needed**.

### Subtype A: Time -> Entity
* **Pattern**: The question provides a specific date (e.g., "on 19 April 2005") and asks "Who" or "Which country" performed an action.
* **Action**: Create a single sub-question (idx: 1) that asks for the entity at that specific time.

### Subtype B: Entity/Action -> Time
* **Pattern**: The question provides an event (e.g., "When did X visit Y?") and asks for the time/date.
* **Action**: Create a single sub-question (idx: 1) that asks for the timestamp of that event.

# General Rules
1.  **Single Step Processing**: Always output a decomposition list containing only one item (`idx: 1`).
2.  **Variant Generation**: Provide exactly **3 distinct variants** of the question.
3.  **Time Normalization**: Normalize them to the international standard ISO 8601 format: YYYY-MM-DD for specific dates, YYYY-MM for year-month precision, and YYYY for year-only precision.
4.  **Entity Type Consistency (CRITICAL)**:
    * You must strictly preserve the interrogative pronoun based on the entity type requested in the original question.
    * If the original question asks for a person, use **"Who"**, **"Whom"**, or **"Whose"**.
    * If the original question asks for a country/nation, use **"Which country"** or **"Which nation"**. Do NOT use "Who" for countries.
    * If the original question asks for an organization or object, use **"Which organization"**, **"Which company"**, or **"What"** appropriately.
    * **Do not generalize specific entity types into generic pronouns (e.g., do not change "Which country" to "Who").**
    * **NEVER use vague terms like "which entity" or "which party".**
5.  **Output Format**: Output strict JSON only. No markdown formatting or extra text.

# Examples

**Example 1 (Subtype B - Action known, find Time):**
Input: When did Qatar pay a visit to Barack Obama?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Qatar pay a visit to Barack Obama?",
            "At what time did Qatar visit Barack Obama?",
            "What is the date of the visit paid by Qatar to Barack Obama?"
        ]
    }},
]

**Example 2 (Subtype A - Time known, find Entity):**
Input: Which country negotiated with Japan on 19 April 2005?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Which country negotiated with Japan on 2005-04-19?",
            "On 2005-04-19, which nation held negotiations with Japan?",
            "What country engaged in negotiations with Japan on the date 2005-04-19?"
        ]
    }}
]

**Example 3 (Subtype A - Time known, find Entity):**
Input: Who visited France in 2009-05?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "Who visited France in 2009-05?",
            "Who made a visit to France in 2009-05?",
            "France host a visit to whom in 2009-05?"
        ]
    }}
]

# Input Data
Please process the following new questions strictly adhering to the logic above:

"""

inference = """# Role
You are an expert Fact-Based Reasoning Engine. Your task is to answer a specific question based **only** on the provided list of "Historical facts".

# Input Format
You will receive:
1.  **Historical facts**: A list of retrieved event strings (Subject - Relation - Object - Timestamp).
2.  **Question**: A natural language query.

# Reasoning Guidelines
1.  **Fact Filtering**: Identify the Subject, Relation (Action), and Object in the question. Filter the "Historical facts" to find matching events.
2.  **Entity Type Validation (CRITICAL)**:
    * Analyze the question to determine the **expected entity type** of the answer.
    * **Person vs. Country**:
        * If the question asks **"Which country"** or **"Which nation"**, you must ONLY output answers that are countries. **Discard** answers that are persons, organizations, or other entities.
        * If the question asks for a person (e.g., **"Which person"**, **"Which leader"**, or **"Who"** in a context implying an individual), you must ONLY output answers that are people. **Discard** answers that are countries or organizations.
    * **Consistency**: Ensure the answer's entity type strictly matches the question's interrogative constraint.
3.  **Temporal Logic**:
    * If the question implies **"first"**, find the earliest date among the matching facts.
    * If the question implies **"last"**, find the latest date among the matching facts.
    * If the question specifies a date (e.g., "on 14 January 2007"), filter for facts happening exactly on that date.
4.  **Answer Extraction**:
    * **Time Answers**: If the question asks "When", "Which year", or "Which month", extract the timestamp.
    * **Entity Answers**: Extract the entity name exactly as it appears in the filtered facts.

# Output Format Rules
You must strictly output a valid JSON object with two keys: `reason` and `answers`.

1.  **"reason"**: A brief explanation of how you derived the answer from the facts, specifically mentioning how you matched the entity type (e.g., "Filtered out 'John Doe' because the question asked for a country...").
2.  **"answers"**: A list of strings.
    * **Date Formatting**:
        * If the question asks for a specific **year**, output format: `"YYYY"`.
        * If the question asks for a specific **month**, output format: `"YYYY-MM"`.
        * If the question asks generally "When" or for the full date, output format: `"YYYY-MM-DD"`.
    * **Entity Formatting**: Output the names exactly as they appear in the facts.

# Examples

**Example 1**
Relevant facts:
Barack Obama Reject Party Member (United Kingdom) 2008-09-23.
Barack Obama Reject Party Member (United Kingdom) 2008-09-23.
Barack Obama Make statement Party Member (United Kingdom) 2008-11-08.
Barack Obama Make statement Party Member (United Kingdom) 2008-11-08.
Barack Obama Express intent to meet or negotiate Party Member (United Kingdom) 2009-03-10.
Zawahiri Reject Barack Obama 2009-08-04.
Question: In which year did barack obama reject the party member of united kingdom?
Output:
{
    "reason": "The facts show 'Barack Obama Reject Party Member (United Kingdom)' occurred on 2008-09-23. The question asks for the year.",
    "answers": ["2008"]
}

**Example 2**
Relevant facts:
Citizen (Africa) Express intent to engage in diplomatic cooperation (such as policy support) Vietnam 2012-09-04.
Vietnam Express intent to engage in diplomatic cooperation (such as policy support) African Union 2008-07-10.
Vietnam Express intent to engage in diplomatic cooperation (such as policy support) African Union 2008-07-28.
Vietnam Express intent to engage in diplomatic cooperation (such as policy support) African Union 2008-07-24.
Vietnam Engage in diplomatic cooperation South Africa 2008-10-27.
Vietnam Engage in diplomatic cooperation South Africa 2005-09-02.
Question: When did the citizens of africa express their intention to establish diplomatic cooperation with vietnam?
Output:
{
    "reason": "Found a direct match: 'Citizen (Africa) Express intent to engage in diplomatic cooperation... Vietnam' on 2012-09-04.",
    "answers": ["2012-09-04"]
}

**Example 3**
Relevant facts:
Media Personnel (Somalia) Praise or endorse Cabinet / Council of Ministers / Advisors (Somalia) 2012-11-27.
Media Personnel (Somalia) Praise or endorse Cabinet / Council of Ministers / Advisors (Somalia) 2015-01-12.
Media Personnel (Somalia) Make statement African Union 2007-10-08.
Media Personnel (Somalia) Make statement African Union 2007-01-17.
Media Personnel (Somalia) Make statement African Union 2012-11-18.
Cabinet / Council of Ministers / Advisors (Somalia) Praise or endorse Media Personnel (Somalia) 2011-11-28.
Media Personnel (Somalia) Make statement African Union 2007-06-15.
Question: When did somalia's media personnel first commend somalia's council of ministers?
Output:
{
    "reason": "There are two facts where Media Personnel (Somalia) praised Cabinet (Somalia): 2012-11-27 and 2015-01-12. The question asks for the 'first' time, which is the earlier date.",
    "answers": ["2012-11-27"]
}

**Example 4**
Relevant facts:
Agence France-Presse Demand China in 2010-05-26.
Agence France-Presse Make an appeal or request China in 2007-01-08.
China Appeal for military aid Agence France-Presse in 2008-03-26.
France Make an appeal or request China in 2012-06-05.
France Demand China in 2008-06-11.
Question: Could you tell me the exact month when Agence France-Presse appealed to China?
Output:
{
    "reason": "Found fact 'Agence France-Presse Make an appeal or request China' on 2007-01-08. The question asks for the exact month.",
    "answers": ["2007-01"]
}

**Example 5**
Relevant facts:
China Make a visit Malaysia in 2007-01-14.
Malaysia Host a visit China in 2007-01-14.
Malaysia Host a visit Pervez Musharraf in 2007-01-31.
Association of Southeast Asian Nations Make a visit Malaysia in 2007-01-14.
Thailand Host a visit Malaysia in 2007-02-14.
China Make a visit Malaysia in 2007-01-26.
Malaysia Host a visit Pervez Musharraf in 2007-01-30.
Malaysia Host a visit Mswati III in 2007-08-14.
Malaysia Host a visit Pervez Musharraf in 2007-02-01.
Malaysia Host a visit China in 2007-01-26.
Pervez Musharraf Make a visit Malaysia in 2007-01-31.
Malaysia Host a visit Association of Southeast Asian Nations in 2007-01-14.
Question: Who visited Malaysia on 14 January 2007?
Output:
{
    "reason": "Identified facts where entities visited Malaysia on 2007-01-14. Matching records found for 'China' and 'Association of Southeast Asian Nations'.",
    "answers": ["China", "Association of Southeast Asian Nations"]
}

"""

