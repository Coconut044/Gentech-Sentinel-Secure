import streamlit as st
import base64
from PIL import Image

def local_css(file_name=r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\style.css"):
    """Injects custom CSS into the Streamlit app."""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Function to add background from local file
def add_bg_from_local(image_file):
    """Adds a background image from a local file."""
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpg;base64,{encoded_string});
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to encode image to base64
def encode_image(image_path):
    """Encodes an image to base64 for embedding in HTML."""
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    return encoded_string

# Dictionary to store background images for each page
background_images = {
    'home': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png",  # Specify the image for the home page
    'aerospace_quiz': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png",  # Add other page-specific images here
    'defence_quiz': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png",
    'cybersecurity_quiz': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png",
    'transportation_quiz': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png",
    'space_quiz': r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Quiz_Bg.png"
}

# Set session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Add the background image based on the current page
current_page = st.session_state.page
if current_page in background_images:
    add_bg_from_local(background_images[current_page])
    
def load_quiz_page(quiz_file_path):
    # Read the file contents
    with open(quiz_file_path, encoding="utf-8") as f:
        quiz_script = f.read()
    
    # Execute the script in the current namespace
    exec(quiz_script, globals())

# Main app code
def main():
    # Load the CSS file
    local_css(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\style.css")  # Ensure that you have a valid CSS file

    # Home page
    if st.session_state.page == 'home':
        st.markdown(
            '''
            <h1 class="title" style="white-space: nowrap; text-align: center;">
                Thales Training System
            </h1>
            ''',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <style>
                .description h3, .description h4 {
                    color: #003366; /* Dark blue color for the headers */
                    text-align: center;
                    font-weight: bold; /* Bold subheaders */
                }
                .description p {
                    text-align: justify;
                    font-size: 16px;
                    color: #003366; /* Dark blue color for paragraph text */
                }
                .description ul {
                    margin-left: 20px;
                    font-size: 15px;
                    color: #003366; /* Dark blue color for list items */
                }
                .description li {
                    margin-bottom: 10px;
                }
            </style>
            <div class="description">
                <h3>Welcome to the Adaptive Cybersecurity Training System</h3>
                <p>
                    Our innovative training platform is designed to provide personalized cybersecurity learning experiences
                    tailored to each department's unique challenges and requirements.
                </p>
                <h4>How It Works:</h4>
                <ul>
                    <li><strong>Preliminary Assessment:</strong> Employees take a dynamically generated, adaptive quiz tailored to their department's domain. 
                    The quiz adjusts its difficulty level in real-time based on the employee's performance, ensuring an optimized evaluation experience.</li>
                    <li><strong>Skill Evaluation:</strong> Quiz performance is analyzed to identify specific cybersecurity knowledge gaps, with adaptive 
                    difficulty providing a more accurate understanding of an employee's technical proficiency.</li>
                    <li><strong>Personalized Learning:</strong> After completing the quiz, employees receive a detailed breakdown of their strengths and weaknesses, 
                    along with customized training modules based on individual and departmental assessment results.</li>
                    <li><strong>Analysis Objectives:</strong>
                        <ul>
                            <li>Technical skill assessment</li>
                            <li>Precise improvement recommendations</li>
                            <li>Targeted learning pathways</li>
                            <li>Professional, constructive tone</li>
                        </ul>
                    </li>
                    <li><strong>Expected Output:</strong>
                        <ul>
                            <li>Detailed strengths analysis</li>
                            <li>Specific skill gap identification</li>
                            <li>Concrete learning recommendations</li>
                            <li>Career development insights</li>
                        </ul>
                    </li>
                    <li><strong>Continuous Improvement:</strong> Learning paths dynamically adapt to employees' progress and incorporate strategies 
                    to address emerging cybersecurity threats, fostering ongoing professional growth.</li>
                </ul>
                <p>Select your department to begin your personalized cybersecurity training journey.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    

        # Department Selection Cards
        st.markdown('<div class="department-container">', unsafe_allow_html=True)

        departments = {
            "Aviation": ("aerospace_quiz", r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\aerospace_image.jpg"),
            "Defence": ("defence_quiz", r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\defence_image.jpg"),
            "Cybersecurity": ("cybersecurity_quiz", r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\cybersecurity_image.jpeg"),
            "Transportation": ("transportation_quiz", r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\transportation_image.jpeg"),
            "Space": ("space_quiz", r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\space_image.jpg"),
        }

        # Create department cards with Streamlit buttons inside
        for department, (page, img_path) in departments.items():
            encoded_image = encode_image(img_path)  # Encode the image to base64
            
            # Layout for the card with Streamlit button inside
            card_html = f"""
            <div class="card" style="display: flex; align-items: center; width: 600px; margin: 20px; padding: 20px; background: rgba(0, 0, 0, 0.7); border-radius: 15px; flex-direction: row; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);">
                <div style="flex: 2; padding-right: 20px;">
                    <h3 style="color: white;">{department}</h3>
                    <p style="color: white;">Click here to start {department} quiz</p>
                </div>
                <div style="flex: 1; text-align: right;">
                    <img src="data:image/jpeg;base64,{encoded_image}" alt="{department} Image" style="width: 200px; height: auto; border-radius: 10px; object-fit: cover;">
                </div>
            </div>
            """
            
            # Display the card in Streamlit
            st.markdown(card_html, unsafe_allow_html=True)

            # Add Streamlit button below the card
            if st.button(f"Start {department} Quiz"):
                st.session_state.page = page  # Update the session state to navigate to the quiz page

        st.markdown('</div>', unsafe_allow_html=True)

    # Redirect to department quiz pages
    elif st.session_state.page == "aerospace_quiz":
        load_quiz_page(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Aviation_Quiz.py")
    elif st.session_state.page == "defence_quiz":
        load_quiz_page(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Defence_Quiz.py")
    elif st.session_state.page == "cybersecurity_quiz":
        load_quiz_page(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Cybersecurity_Quiz.py")
    elif st.session_state.page == "transportation_quiz":
        load_quiz_page(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Transportation_Quiz.py")
    elif st.session_state.page == "space_quiz":
        load_quiz_page(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Space_Quiz.py")
        
    

if __name__ == "__main__":
    main()
