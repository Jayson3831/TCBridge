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
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
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

**Example 4:**
Input: Who was the first to visit Japan after the Russian Union of Industrialists and Entrepreneurs?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did the Russian Union of Industrialists and Entrepreneurs visit Japan?",
            "At what time did the Russian Union of Industrialists and Entrepreneurs visit Japan?",
            "What is the date when the Russian Union of Industrialists and Entrepreneurs visited Japan?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was the first to visit Japan after #1?",
            "After #1, who was the first to visit Japan?",
            "Who visited Japan first after #1?"
        ]
    }},
]

**Example 5:**
Input: Who was the first to investigate France after Sean R. Parnell?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Sean R. Parnell investigate France?",
            "At what time did Sean R. Parnell investigate France?",
            "What is the date when Sean R. Parnell investigated France?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was the first to investigate France after #1?",
            "After #1, who was the first to investigate France?",
            "Who investigated France first after #1?"
        ]
    }},
]

**Example 6:**
Input: Which country was the first to sign an agreement with South Korea after Eletrobras?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Eletrobras sign an agreement with South Korea?",
            "At what time did Eletrobras sign an agreement with South Korea?",
            "What is the date when Eletrobras signed an agreement with South Korea?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country was the first to sign an agreement with South Korea after #1?",
            "After #1, which country was the first to sign an agreement with South Korea?",
            "Which country signed an agreement with South Korea first after #1?"
        ]
    }},
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
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
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

**Example 4:**
Input: Before Tony Blair, which country last did France decline?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did France decline Tony Blair?",
            "At what time did France decline Tony Blair?",
            "What is the date when France declined Tony Blair?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country did France decline last before #1?",
            "Before #1, which country did France decline last?",
            "Which country was the last that France declined before #1?"
        ]
    }},
]

**Example 5:**
Input: Who was the last person Winston Peters wanted to meet before Timor-Leste?
Output:
[
    {{
        "subq_idx": 1,
        "variations": [
            "When did Winston Peters want to meet Timor-Leste?",
            "At what time did Winston Peters want to meet Timor-Leste?",
            "What is the date when Winston Peters wanted to meet Timor-Leste?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Who was the last person Winston Peters wanted to meet before #1?",
            "Before #1, who was the last person Winston Peters wanted to meet?",
            "Who did Winston Peters want to meet last before #1?"
        ]
    }},
]

**Example 6:**
Input: Before Ali Muhammad Mujawar, which country last recommended Japan?
Output:
[
    {{
        "subq_idx": 1,
        "variants": [
            "When did Ali Muhammad Mujawar recommend Japan?",
            "At what time did Ali Muhammad Mujawar recommend Japan?",
            "What is the date when Ali Muhammad Mujawar recommended Japan?"
        ]
    }},
    {{
        "subq_idx": 2,
        "variants": [
            "Which country last recommended Japan before #1?",
            "Before #1, which country last recommended Japan?",
            "Which country was the last to recommend Japan before #1?"
        ]
    }},
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
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
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
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
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
    * **NEVER use vague terms like "the entity", "the party", or "the group".**
    * Strictly preserve the specific names of entities mentioned (e.g., if the input is "Iran", do not change it to "the country" or "the nation" unless absolutely necessary for flow, and NEVER genericize it to "the entity").
    * Preserve the specific action verbs or their precise synonyms (e.g., "praise" -> "commend", "express approval", but NOT vague terms like "interact with").
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
You are an expert Fact-Based Reasoning Engine. Your task is to answer the **Raw Question** based on the provided context.

# Context Structure
You will receive a context block containing:
1.  **Raw Question**: The user's original complex query.
2.  **Subquestions**: A logical decomposition of the original question. Use these to understand the steps required to solve the problem (e.g., finding a time anchor first).
3.  **Relevant Facts**: A list of retrieved historical events (Subject - Relation - Object - Timestamp) associated with each subquestion.

# Reasoning Guidelines
1.  **Analyze the Logic**: Look at the `Subquestions` to determine the logical flow (e.g., "Find date of Event A" -> "Find Event B that happened after Event A").
2.  **Filter Facts**: Strictly use the provided `Relevant Facts`. Do not hallucinate external knowledge.
    * Pay close attention to **Subject** and **Object** directionality (e.g., "A accuse B" is different from "B accuse A").
    * Pay close attention to **Action** types (e.g., "Praise" vs "Criticize").
3.  **Temporal Reasoning**:
    * **First/Last**: Compare timestamps to find the earliest or latest event matching the criteria.
    * **Before/After**: Filter events based on the timestamp derived from the anchor event.
    * **Same Time**: Match events occurring in the same specific year, month, or day.
4.  **Formatting**:
    * **Time**: If asking for a year/month/day, extract it from the ISO date (YYYY/YYYY-MM/YYYY-MM-DD).
    * **Entities**: Output entity names exactly as they appear in the facts.
5.  **Critical Constraint - Answer Presence**:
    * **MUST** verify that the answer event exists in the provided `Relevant Facts`.
    * If the `Relevant Facts` do NOT contain any event that answers the question (e.g., no matching entities, no matching time period, or no matching action), you MUST return an empty list for `"answers"`.
    * **DO NOT** guess, hallucinate, or infer answers from external knowledge when the facts are insufficient.
    * When returning an empty list, explain in `"reason"` that the relevant facts do not contain the answer.

# Output Format
Output a valid JSON object with two keys:
* `"reason"`: A concise step-by-step explanation of how you derived the answer from the facts.
* `"answers"`: A list of strings containing the final answers.

# Examples

**Example 1**
**Raw question**: Could you tell me the exact month when the European Central Bank hosted the visit of Nicos Anastasiades?
**Subquestion 1**: What is the month when the European Central Bank hosted Nicos Anastasiades's visit?
**Relevant facts 1**: 
European Central Bank Host a visit Nicos Anastasiades in 2013-07-03.
Nicos Anastasiades Make a visit European Central Bank in 2013-07-03.
China Host a visit Nicos Anastasiades in 2015-10-19.
China Host a visit Nicos Anastasiades in 2015-10-18.
Nicos Anastasiades Host a visit Angela Merkel in 2014-05-06.
**Output**:
{{
	"reason": "The relevant fact shows 'European Central Bank Host a visit Nicos Anastasiades' occurred on 2013-07-03. The question asks for the exact month.",
	"answers": ["2013-07"]
}}

**Example 2**
**Raw question**: After the UN Security Council, to whom did Tony Blair first express optimism?
**Subquestion 1**: What is the date when Tony Blair expressed optimism to the UN Security Council?
**Relevant facts 1**:
Tony Blair Make optimistic comment UN Security Council in 2005-09-13.
**Subquestion 2**: Who was the first to receive optimism expressed by Tony Blair after 2005-09-13?
**Relevant facts 2**:
Tony Blair Express intent to meet or negotiate China in 2005-09-01.
Tony Blair Make optimistic comment African Union in 2005-01-23.
Citizen (United Kingdom) Make optimistic comment Tony Blair in 2006-09-09.
Tony Blair Make optimistic comment Government (Germany) in 2005-10-11.
Tony Blair Express intent to meet or negotiate Elizabeth II in 2005-04-05.
Tony Blair Express intent to meet or negotiate Iran in 2005-11-23.
**Output**:
{{
	"reason": "First, the anchor event (Blair optimism to UN Security Council) occurred on 2005-09-13. I need to find who Tony Blair made an optimistic comment to *after* this date. Comparing the facts: African Union (Jan 2005) is before. Optimism to Government (Germany) occurred on 2005-10-11. This is the first instance after Sep 13.",
	"answers": ["Government (Germany)"]
}}

**Example 3**
**Raw question**: In what year did the women of Australia first accuse the Lawyer/Attorney of Australia?
**Subquestion 1**: When did the women of Australia initially make accusations against the Lawyer/Attorney of Australia?
**Relevant facts 1**:
Women (Australia) Accuse Lawyer/Attorney (Australia) in 2014-03-11.
Lawyer/Attorney (Australia) Accuse Women (Australia) in 2007-03-28.
Lawyer/Attorney (Australia) Accuse Women (Australia) in 2013-07-31.
Lawyer/Attorney (Australia) Accuse Women (Australia) in 2013-03-26.
Lawyer/Attorney (Australia) Accuse Women (Australia) in 2012-06-26.
**Output**:
{{
    "reason": "The question asks when 'Women (Australia)' accused 'Lawyer/Attorney (Australia)'. Most facts show the Lawyer accusing the Women. There is only one fact where Women are the subject accusing the Lawyer: 'Women (Australia) Accuse Lawyer/Attorney (Australia) in 2014-03-11'. The year is 2014.",
	"answers": ["2014"]
}}

**Example 4**
**Raw question**: Who was the last person Roh Moo Hyun wanted to negotiate with before the head of government of Peru?
**Subquestion 1**: What is the date when Roh Moo Hyun wanted to negotiate with the head of government of Peru?
**Relevant facts 1**:
Roh Moo Hyun Express intent to meet or negotiate Head of Government (Peru) in 2005-10-31.
**Subquestion 2**: Who did Roh Moo Hyun want to negotiate with last before 2005-10-31?
**Relevant facts 2**:
Roh Moo Hyun Express intent to meet or negotiate Japan in 2005-11-21.
Roh Moo Hyun Express intent to meet or negotiate Mexico in 2005-05-05.
Roh Moo Hyun Express intent to meet or negotiate South Korea in 2005-05-25.
Roh Moo Hyun Express intent to meet or negotiate South Korea in 2005-10-26.
Roh Moo Hyun Express intent to meet or negotiate South Korea in 2005-11-05.
Roh Moo Hyun Express intent to meet or negotiate South Korea in 2005-11-09.
Roh Moo Hyun Express intent to meet or negotiate Japan in 2005-09-22.
Roh Moo Hyun Express intent to meet or negotiate Mexico in 2005-08-22.
Roh Moo Hyun Express intent to meet or negotiate Mexico in 2005-08-23.
**Output**:
{{
	"reason": "The anchor event is Roh Moo Hyun negotiating with Head of Government (Peru) on 2005-10-31. I need the latest event *before* this date. Japan (Nov 21) and South Korea (Nov 05) are after. Among those before, South Korea on 2005-10-26 is closer to 10-31 than Japan (Sep 22) or other South Korea dates.",
	"answers": ["South Korea"]
}}

**Example 5**
**Raw question**: Who did the citizens of Norway want to negotiate with after 14 June 2006?
**Subquestion 1**: After 2006-06-14, with whom did the citizens of Norway desire to negotiate?
**Relevant facts 1**:
Citizen (Norway) Express intent to meet or negotiate Education (Norway) in 2006-06-14.
Citizen (Norway) Express intent to meet or negotiate Anders Breivik in 2012-06-18.
Citizen (North Korea) Express intent to meet or negotiate South Korea in 2006-08-24.
Citizen (Norway) Express intent to meet or negotiate South Korea in 2007-05-07.
Citizen (Norway) Express intent to meet or negotiate Iraq in 2014-10-30.
Citizen (North Korea) Express intent to meet or negotiate Japan in 2006-04-06.
**Output**:
{{
	"reason": "The time constraint is strictly 'after 2006-06-14'. Checking Citizen (Norway) intentions: Education (Norway) is *on* the date (not after). Anders Breivik (2012), South Korea (2007), and Iraq (2014) are all after the date.",
	"answers": ["Anders Breivik", "South Korea", "Iraq"]
}}

**Example 6**
**Raw question**: Who gave a condemnation of Boko Haram in the same month as the Ministry of Iran?
**Subquestion 1**: What is the date when the Ministry of Iran condemned Boko Haram?
**Relevant facts 1**:
Ministry (Iran) Criticize or denounce Boko Haram in 2014-05-21.
**Subquestion 2**: Who gave a condemnation of Boko Haram in the same month as 2014-05-21?
**Relevant facts 2**:
UN Security Council Criticize or denounce Boko Haram in 2014-05-11.
Barack Obama Criticize or denounce Boko Haram in 2014-05-12.
Iran Criticize or denounce Boko Haram in 2014-05-21.
UN Security Council Criticize or denounce Boko Haram in 2014-05-10.
ANC Youth League Criticize or denounce Boko Haram in 2014-05-21.
Al-Shabaab Praise or endorse Boko Haram in 2014-05-19.
Media (Nigeria) Criticize or denounce Boko Haram in 2014-04-21.
Education (Nigeria) Criticize or denounce Boko Haram in 2014-05-26.
Citizen (Nigeria) Criticize or denounce Boko Haram in 2014-05-07.
Citizen (Saudi Arabia) Criticize or denounce Boko Haram in 2014-05-10.
African Union Criticize or denounce Boko Haram in 2015-01-13.
Chris Olukolade Criticize or denounce Boko Haram in 2014-03-15.
**Output**:
{{
	"reason": "The Ministry (Iran) condemned Boko Haram in 2014-05. I need to find other entities who 'Criticize or denounce' Boko Haram in May 2014. Matches: UN Security Council, Barack Obama, Iran, ANC Youth League, Citizen (Nigeria), Citizen (Saudi Arabia), Education (Nigeria). Excluded 'Al-Shabaab' (Praise) and 'Media (Nigeria)' (April).",
	"answers": ["UN Security Council", "Barack Obama", "Iran", "ANC Youth League", "Citizen (Nigeria)", "Citizen (Saudi Arabia)", "Education (Nigeria)"]
}}

**Example 7**
**Raw question**: With whom did Wen Jiabao first express interest in cooperation in 2006?
**Subquestion 1**: In 2006, with whom did Wen Jiabao first express interest in cooperating?
**Relevant facts 1**:
Wen Jiabao Investigate China in 2006-10-11.
Wen Jiabao Investigate China in 2006-07-16.
Huang Ju Consult Wen Jiabao in 2006-07-13.
Wen Jiabao Express intent to cooperate Angela Merkel in 2006-03-02.
Jakaya Mrisho Kikwete Consult Wen Jiabao in 2006-11-04.
China Consult Wen Jiabao in 2006-02-25.
China Consult Wen Jiabao in 2006-03-10.
Wen Jiabao Investigate China in 2006-07-23.
**Output**:
{{
	"reason": "The question specifies the action 'express interest in cooperation' in 2006. While there are earlier events involving 'Consult' or 'Investigate', the only fact explicitly matching 'Express intent to cooperate' is with Angela Merkel on 2006-03-02.",
	"answers": ["Angela Merkel"]
}}

**Example 8**
**Raw question**: Who criticised the business of Argentina in the same year of the Senate of Argentina?
**Subquestion 1**: In which year did the Senate of Argentina criticise the business of Argentina?
**Relevant facts 1**:
Senate (Argentina) Criticize or denounce Business (Argentina) in 2011-03-04.
**Subquestion 1**: Who criticised the business of Argentina in the same year as 2011-03-04?
**Relevant facts 1**:
Cristina Fernández de Kirchner Criticize or denounce Business (Argentina) in 2011-04-19.
Argentine Industrial Union Criticize or denounce China in 2015-02-03.
Economist (Mexico) Criticize or denounce National Action Party in 2011-03-21.
Cristina Fernández de Kirchner Criticize or denounce Business (Argentina) in 2012-01-25.
Lawyer/Attorney (Argentina) Criticize or denounce Cristina Fernández de Kirchner in 2011-07-21.
National Action Party Criticize or denounce Mexico in 2012-04-11.
Lawmaker (Argentina) Criticize or denounce Daniel Scioli in 2011-04-14.
**Output**:
{{
	"reason": "The Senate of Argentina criticized Business (Argentina) in 2011. I need to find others who criticized 'Business (Argentina)' in 2011. Cristina Fernández de Kirchner did so on 2011-04-19. Other facts involve different targets (China, National Action Party) or different years (2012, 2015).",
	"answers": ["Cristina Fernández de Kirchner"]
}}

"""


fallback = """# Role
You are an expert historian assistant. Your task is to answer the user's question based ONLY on the provided [Relevant facts].

# Core Logic & Constraints
1. Semantic Relevance: Strictly match semantic meaning. For example, "Business (South Korea)" CANNOT be equated with "South Korea", and "appeal or request" CANNOT be equated with "consult".
2. Full Names: Always retrieve the full, explicit name of entities. Do not use partial names or abbreviations inside parentheses.
3. Time Logic: 
   - Handle conditions like "before", "after", "first", or "last" carefully by comparing timestamps.
   - If multiple sources provide valid answers, return the union of all correct answers.

# Output Format Rules
You must strictly output a valid JSON object with two keys: `reason` and `answers`.

1.  **"reason"**: A brief explanation of how you derived the answer from the facts.
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
    "reason": "The rejection event occurred on 2008-09-23, so the year is 2008.",
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
    "reason": "From the historical facts: Citizen (Africa) Express intent to engage in diplomatic cooperation (such as policy support) Vietnam 2012-09-04. This matches exactly what the question asks: citizens of Africa expressing intent toward diplomatic cooperation with Vietnam. So the date is 2012-09-04.",
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
    "reason": "We are asked to find the first time Somalia's media personnel commended (i.e., praised or endorsed) Somalia's Cabinet / Council of Ministers / Advisors. From the historical facts: Media Personnel (Somalia) Praise or endorse Cabinet / Council of Ministers / Advisors (Somalia) on: 2012-11-27 and 2015-01-12. Among these, the earliest instance is 2012-11-27.",
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
    "reason": "The user asks for the month Agence France-Presse appealed to China. I filtered out facts where the subject was 'France' or 'China'. The specific fact 'Agence France-Presse Make an appeal or request China in 2007-01-08' is the correct match. So the answer is: 2007-01.",
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
    "reason": "Both China and Association of Southeast Asian Nations visited on that exact date. So the answer is: "China", "Association of Southeast Asian Nations",
    "answers": ["China", "Association of Southeast Asian Nations"]
}

"""

