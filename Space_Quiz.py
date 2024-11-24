import streamlit as st
import google.generativeai as genai
import time
import base64

# Apply custom CSS to make all text dark blue except for button text
st.markdown(
    """
    <style>
    body, h1, h2, h3, h4, h5, h6, p, label, div {
        color: #003366 !important;  /* Dark blue color for text */
    }
    .stButton>button {
        background-color: #003366;
        color: white;  /* Button text stays white */
        font-size: 16px;
        border-radius: 8px;
        padding: 10px;
        margin: auto;
        display: block;
    }
    .stButton>button:hover {
        background-color: #0055a4;
    }
    .quiz-question {
        font-size: 20px;
        font-weight: bold;
        color: #003366;  /* Dark blue for questions */
    }
    /* Special styling for Submit and Next buttons */
    .stButton>button[kind="secondary"] {
        background-color: #f0f2f6;
        color: #003366;
        border: 2px solid #003366;
        font-weight: bold;
        width: 200px;  /* Fixed width for consistency */
        margin: 10px auto;
        transition: all 0.3s ease;
    }
    .stButton>button[kind="secondary"]:hover {
        background-color: #e0e2e6;
        transform: scale(1.02);
    }
    /* Style for radio button text */
    .st-emotion-cache-1y4p8pa {
        color: #003366 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configure Gemini API (Replace with your actual API key)
genai.configure(api_key="AIzaSyA6ZmdEiIbH5nt_dPQEc1cuCH2_T0uBwVo")

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

# Load and encode the background image as base64
def get_base64_of_bin_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Set background image
def set_background_image(base64_string):
    background_style = f"""
    <style>
        .stApp {{
            background: url("data:image/png;base64,{base64_string}");
            background-size: cover;
        }}
    </style>
    """
    st.markdown(background_style, unsafe_allow_html=True)

# Add custom CSS for styling
def add_custom_styles():
    custom_css = """
    <style>
        h1, h2, h3 {
            text-align: center;
            font-family: 'Arial', sans-serif;
            color: #003366;
        }
        .stButton>button {
            background-color: #003366;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px;
            margin: auto;
            display: block;
        }
        .stButton>button:hover {
            background-color: #0055a4;
        }
        .quiz-question {
            font-size: 20px;
            font-weight: bold;
            color: #003366;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# Safely generate content
def safe_generate_content(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7,
                    top_p=1.0
                )
            )
            if response.parts:
                return response.text
        except Exception as e:
            st.error(f"Error in generation attempt {attempt + 1}: {e}")
            time.sleep(2)
    return None

# Generate quiz question
def generate_quiz_question(difficulty):
    prompt = f"""
    Generate a precise, factual multiple-choice question about space cybersecurity.
    Specific Requirements:
    - Difficulty Level: {difficulty}
    - Focus: Technical, verifiable cybersecurity concepts
    - Avoid speculative or potentially dangerous scenarios

    Question Format:
    - Clear, concise technical question
    - 4 professional, technically accurate options
    - One definitively correct answer
    - Brief, educational explanation

    Example Output Structure:
    {{
        "question": "What is a critical role of cybersecurity in space missions?",
        "options": [
            "Securing satellite communication from cyber threats",
            "Improving the physical durability of spacecraft",
            "Enhancing fuel efficiency of rockets",
            "Monitoring the trajectory of asteroids"
        ],
        "correct_answer": 0,
        "explanation": "Cybersecurity in space missions ensures the protection of satellite communication systems from cyber threats, which is vital for maintaining data integrity and mission success."
    }}

    Provide ONLY the JSON-formatted response. No additional text.
    """
    response_text = safe_generate_content(prompt)
    if response_text:
        try:
            return eval(response_text)
        except Exception as e:
            st.error(f"Parsing error: {e}")
            return None
    return None

# Determine next difficulty
def determine_next_difficulty(current_difficulty, is_correct):
    difficulty_levels = ['easy', 'medium', 'hard']
    current_index = difficulty_levels.index(current_difficulty)
    if is_correct and current_index < len(difficulty_levels) - 1:
        return difficulty_levels[current_index + 1]
    elif not is_correct and current_index > 0:
        return difficulty_levels[current_index - 1]
    return current_difficulty

# Generate performance analysis
def generate_performance_analysis(score_percentage, missed_topics):
    prompt = f"""
    Provide a professional, technical performance analysis for a space cybersecurity assessment:
    Performance Data:
    - Total Score: {score_percentage}%
    - Missed Technical Areas: {', '.join(missed_topics)}

    Analysis Objectives:
    - Technical skill assessment
    - Precise improvement recommendations
    - Targeted learning pathways
    - Professional, constructive tone

    Expected Output:
    - Detailed strengths analysis
    - Specific skill gap identification
    - Concrete learning recommendations
    - Career development insights
    """
    return safe_generate_content(prompt)

# Main application
def main():
    st.title("🛸Space Cybersecurity Quiz")
    st.subheader("Test your knowledge and learn as you go!")

    # Apply custom styles and background
    add_custom_styles()
    set_background_image(get_base64_of_bin_file(r"Quiz_Bg.png"))

    # Initialize session state
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.current_question = 0
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.current_difficulty = 'medium'
        st.session_state.selected_answer = None
        st.session_state.answer_submitted = False

    if not st.session_state.quiz_started:
        if st.button("Start Quiz"):
            st.session_state.quiz_started = True

    if st.session_state.quiz_started and st.session_state.current_question < 10:
        while len(st.session_state.questions) < 10:
            question = generate_quiz_question(st.session_state.current_difficulty)
            if question:
                st.session_state.questions.append(question)

        current_q = st.session_state.questions[st.session_state.current_question]
        st.markdown(f'<p class="quiz-question">Question {st.session_state.current_question + 1}: {current_q["question"]}</p>', unsafe_allow_html=True)

        st.session_state.selected_answer = st.radio(
            "Select your answer:",
            current_q['options'],
            index=None
        )

        if st.button("Submit Answer"):
            if st.session_state.selected_answer is not None:
                correct_answer = current_q['options'][current_q['correct_answer']]
                is_correct = st.session_state.selected_answer == correct_answer
                st.session_state.answers.append(is_correct)
                st.session_state.answer_submitted = True

                if is_correct:
                    st.success("Correct! 🎉")
                else:
                    st.error(f"Incorrect. The correct answer is: {correct_answer}")
                st.write("Explanation:", current_q['explanation'])
                st.session_state.current_difficulty = determine_next_difficulty(
                    st.session_state.current_difficulty,
                    is_correct
                )
            else:
                st.warning("Please select an answer before submitting.")

        if st.session_state.answer_submitted:
            if st.button("Go to Next Question"):
                st.session_state.current_question += 1
                st.session_state.answer_submitted = False
                st.session_state.selected_answer = None

    if st.session_state.current_question >= 10:
        score_percentage = (sum(st.session_state.answers) / 10) * 100
        st.header("🏆 Quiz Results")
        st.metric("Your Score", f"{score_percentage:.2f}%")

        missed_topics = [
            st.session_state.questions[i]['question']
            for i, correct in enumerate(st.session_state.answers)
            if not correct
        ]

        analysis = generate_performance_analysis(score_percentage, missed_topics)

        st.markdown("## Performance Analysis")
        st.write(analysis)

if __name__ == "__main__":
    main()
