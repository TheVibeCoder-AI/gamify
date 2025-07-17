import streamlit as st
import json
import openai
import re
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional
import time
import hashlib

# Initialize OpenAI client
def initialize_openai():
    if 'openai_client' not in st.session_state:
        api_key = st.text_input("Enter OpenAI API Key", type="password")
        if api_key:
            st.session_state.openai_client = openai.OpenAI(api_key=api_key)
        else:
            st.error("Please provide a valid OpenAI API key")
            st.stop()
        

# Configuration Data
PERSONAS_CONFIG = {
    "tom_carter": {
        "name": "Tom Carter",
        "age": 28,
        "occupation": "Freelance Designer",
        "income_range": "£35,000-£45,000",
        "current_products": ["Savings Account"],
        "financial_status": "Emerging Professional",
        "risk_profile": "Moderate",
        "avatar": "🎨"
    },
    "sarah_johnson": {
        "name": "Sarah Johnson",
        "age": 24,
        "occupation": "Graduate Trainee",
        "income_range": "£22,000-£28,000",
        "current_products": ["Current Account"],
        "financial_status": "Early Career",
        "risk_profile": "Conservative",
        "avatar": "🎓"
    },
    "mike_rodriguez": {
        "name": "Mike Rodriguez",
        "age": 32,
        "occupation": "Software Engineer",
        "income_range": "£55,000-£70,000",
        "current_products": ["Savings Account", "Credit Card"],
        "financial_status": "Established Professional",
        "risk_profile": "Aggressive",
        "avatar": "💻"
    }
}

# Available products for dropdown
AVAILABLE_PRODUCTS = ["Savings Account", "Current Account", "Credit Card", "Investment Account", "Loan"]

# Enhanced base goal categories with health insurance priority
BASE_GOAL_CATEGORIES = [
    "Health Insurance Coverage",  # Highest priority
    "Emergency Fund Building",
    "Income Protection",
    "Debt Management",
    "Investment Planning",
    "Retirement Planning",
    "Life Insurance Coverage",
    "Financial Education"
]

class AIAgentManager:
    def __init__(self, client):
        self.client = client
    
    def get_completion(self, messages, temperature=0.7, max_tokens=800):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"AI Agent Error: {str(e)}")
            return None

class GoalCoachAgent(AIAgentManager):
    def generate_personalized_goals(self, persona_data):
        messages = [
            {"role": "system", "content": f"""You are an expert Goal Coach Agent for Lloyds Bank's LifeQuest platform. 
            Generate 4-6 highly personalized financial goals based on the user's profile. 
            
            IMPORTANT PRIORITIES:
            1. Health Insurance should ALWAYS be the highest priority goal for all users
            2. Emergency Fund should be second priority for users without significant savings
            3. Consider age-appropriate goals (younger users focus on insurance/emergency funds, older users on investments)
            
            User Profile:
            - Name: {persona_data['name']}
            - Age: {persona_data['age']} 
            - Occupation: {persona_data['occupation']}
            - Income: {persona_data['income_range']}
            - Current Products: {persona_data['current_products']}
            - Financial Status: {persona_data['financial_status']}
            - Risk Profile: {persona_data['risk_profile']}
            
            Generate diverse, realistic goals that match their life stage and financial situation.
            For target amounts, use realistic figures based on their income range.
            
            Return ONLY a JSON array of goals in this exact format:
            [
                {{
                    "id": "goal_1",
                    "title": "Get Comprehensive Health Insurance",
                    "description": "Secure health insurance coverage to protect against medical expenses",
                    "priority": "High",
                    "timeline": "Short term",
                    "category": "Health Insurance Coverage",
                    "target_amount": 2000,
                    "difficulty": "Beginner",
                    "why_important": "Health insurance is essential for financial security and peace of mind"
                }}
            ]
            
            Make each goal specific to their situation, not generic."""},
            {"role": "user", "content": "Generate personalized financial goals for this user profile."}
        ]
        
        response = self.get_completion(messages, temperature=0.8)
        if response:
            try:
                response_clean = self._clean_json_response(response)
                goals = json.loads(response_clean)
                goals = self._prioritize_health_insurance(goals)
                return goals
            except json.JSONDecodeError:
                st.error("Error parsing AI response for goals")
                return self._get_default_goals_for_persona(persona_data)
        return self._get_default_goals_for_persona(persona_data)
    
    def _clean_json_response(self, response):
        match = re.search(r'```json(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def _prioritize_health_insurance(self, goals):
        health_goals = [g for g in goals if 'health' in g.get('category', '').lower()]
        other_goals = [g for g in goals if 'health' not in g.get('category', '').lower()]
        if not health_goals:
            health_goal = {
                "id": "goal_health",
                "title": "Get Comprehensive Health Insurance",
                "description": "Secure health insurance coverage to protect against medical expenses",
                "priority": "High",
                "timeline": "Short term",
                "category": "Health Insurance Coverage",
                "target_amount": "2000",
                "difficulty": "Beginner",
                "why_important": "Health insurance is essential for financial security"
            }
            return [health_goal] + other_goals
        return health_goals + other_goals
    
    def _get_default_goals_for_persona(self, persona_data):
        base_goals = [
            {
                "id": "goal_health",
                "title": "Get Comprehensive Health Insurance",
                "description": "Secure health insurance coverage to protect against medical expenses",
                "priority": "High",
                "timeline": "Short term",
                "category": "Health Insurance Coverage",
                "target_amount": 2000,
                "difficulty": "Beginner",
                "why_important": "Health insurance is essential for financial security"
            },
            {
                "id": "goal_emergency",
                "title": "Build Emergency Fund",
                "description": "Create a financial safety net covering 3-6 months of expenses",
                "priority": "High",
                "timeline": "Medium term",
                "category": "Emergency Fund Building",
                "target_amount": 10000,
                "difficulty": "Beginner",
                "why_important": "Emergency funds provide financial stability during unexpected situations"
            }
        ]
        if persona_data['age'] < 30:
            base_goals.append({
                "id": "goal_life_insurance",
                "title": "Get Life Insurance Coverage",
                "description": "Secure life insurance to protect dependents and future financial obligations",
                "priority": "Medium",
                "timeline": "Short term",
                "category": "Life Insurance Coverage",
                "target_amount": 1500,
                "difficulty": "Beginner",
                "why_important": "Life insurance provides financial protection for loved ones"
            })
        else:
            base_goals.append({
                "id": "goal_investment",
                "title": "Start Investment Portfolio",
                "description": "Begin investing for long-term wealth building and financial goals",
                "priority": "Medium",
                "timeline": "Medium term",
                "category": "Investment Planning",
                "target_amount": 5000,
                "difficulty": "Intermediate",
                "why_important": "Investments help grow wealth and beat inflation over time"
            })
        return base_goals

class QuestAgent(AIAgentManager):
    def __init__(self, client):
        super().__init__(client)
        self.quest_counter = 0

    def generate_quests_for_goal(self, goal_data, persona_data, completed_quests_count=0):
        quest_stage = self._determine_quest_stage(completed_quests_count)
        health_goal = goal_data['category'].lower() == "health insurance"

        messages = [
            {
                "role": "system",
                "content": f"""
    You are a Quest Agent for Lloyds Bank's LifeQuest platform.
    Generate 6-8 UNIQUE, engaging quests specifically for the selected 3 quizes compulsory.

    GOAL DETAILS:
    - Title: {goal_data['title']}
    - Description: {goal_data['description']}
    - Category: {goal_data['category']}
    - Target Amount: £{goal_data.get('target_amount', 0)}
    - Priority: {goal_data['priority']}

    USER PROFILE:
    - Name: {persona_data['name']}
    - Age: {persona_data['age']}
    - Occupation: {persona_data['occupation']}
    - Income: {persona_data['income_range']}
    - Risk Profile: {persona_data['risk_profile']}

    QUEST STAGE: {quest_stage}
    Completed Quests: {completed_quests_count}

    QUEST GENERATION RULES:
    1. Create quests that are DIRECTLY related to achieving this specific goal.
    2. Include a mix of: learning (40%), action (30%), quiz (20%), challenge (10%).
    3. For {quest_stage} stage, focus on: {self._get_stage_focus(quest_stage)}
    4. Each quest must be unique and build on the user's prior knowledge.
    5. Include real Lloyds Bank products and services where relevant.

    ⚠️ SPECIAL RULE for HEALTH INSURANCE:
    If the goal category is Health Insurance, you MUST include at least 3 quiz-type quests COMPULS0RY. These should test the user's understanding of:
    - Basics of health insurance (terms, coverage, exclusions)
    - Comparison of plans (e.g., individual vs. family)
    - Practical scenarios (e.g., claim process, waiting periods)

    You may exceed the usual type distribution if needed to meet this requirement OF ADDING ATLEAST 3 QUIZES.

    EXAMPLES of Health Insurance Quests:
    - Learning: “How health insurance works in the UK”
    - Action: “Use Lloyds Health Calculator to estimate your premium”
    - Quiz: “What does ‘deductible’ mean?” with 4 options
    - Quiz: “Which plan suits a freelancer best?”
    - Quiz: “Which conditions are usually not covered?”

    QUEST PROGRESSION:
    - Beginner: Basic education and awareness
    - Intermediate: Practical steps and comparisons
    - Advanced: Action items like trials, account setup, product purchases

    Return ONLY a JSON array of quests like this:

    [
        {{
            "id": "quest_[unique_id]",
            "title": "Quest Title",
            "description": "Specific description related to the goal",
            "type": "learning/action/quiz/challenge",
            "points": 100-300,
            "difficulty": "Easy/Medium/Hard",
            "estimated_time": "1-2 minutes",
            "unlock_reward": "Specific reward related to goal",
            "goal_category": "{goal_data['category']}",
            "learning_content": "For learning quests, provide 2–3 short but rich paragraphs explaining the topic in a friendly, educational tone. Use real examples, clarify key terms (e.g. premium, deductible), and make the user feel informed. Avoid robotic or one-liner definitions.",
            "action_steps": ["Step 1", "Step 2"] (only for action type),
            "questions": [
                {{
                    "question": "Goal-specific question?",
                    "options": ["A", "B", "C", "D"],
                    "correct": 0,
                    "explanation": "Why this is correct"
                }}
            ] (only for quiz type)
        }}
    ]
    """
            },
            {
                "role": "user",
                "content": f"Generate {quest_stage} quests specifically for achieving the goal: {goal_data['title']}"
            }
        ]



        response = self.get_completion(messages, temperature=0.8, max_tokens=1200)
        if response:
            try:
                response_clean = self._clean_json_response(response)
                quests = json.loads(response_clean)
                for i, quest in enumerate(quests):
                    quest['id'] = f"quest_{goal_data['id']}_{quest_stage}_{i}_{int(time.time())}"
                    quest['goal_id'] = goal_data['id']
                    quest['stage'] = quest_stage
                return quests
            except json.JSONDecodeError:
                st.error("Error parsing AI response for quests")
                return self._get_default_quests_for_goal(goal_data)
        return self._get_default_quests_for_goal(goal_data)
    
    def generate_progressive_quests(self, goal_data, persona_data, completed_quests_count):
        if completed_quests_count < 3:
            return self.generate_quests_for_goal(goal_data, persona_data, completed_quests_count)
        messages = [
            {"role": "system", "content": f"""Generate 3-5 ADVANCED action quests for users who have completed {completed_quests_count} quests.
            These should be practical action items like:
            - "Try Lloyds Health Insurance Free Trial"
            - "Set up Lloyds Premium Savings Account"
            - "Use Lloyds Investment Calculator"
            - "Purchase {goal_data['category']} Product"
            - "Schedule Financial Consultation"
            
            Goal: {goal_data['title']}
            Category: {goal_data['category']}
            
            Make quests actionable and specific to Lloyds Bank products."""},
            {"role": "user", "content": f"Generate advanced action quests for {goal_data['title']}"}
        ]
        
        response = self.get_completion(messages, temperature=0.7)
        if response:
            try:
                response_clean = self._clean_json_response(response)
                quests = json.loads(response_clean)
                for i, quest in enumerate(quests):
                    quest['id'] = f"quest_{goal_data['id']}_advanced_{i}_{int(time.time())}"
                    quest['goal_id'] = goal_data['id']
                    quest['stage'] = "advanced"
                    quest['type'] = "action"
                    quest['points'] = quest.get('points', 250)
                return quests
            except:
                return []
        return []
    
    def _determine_quest_stage(self, completed_count):
        if completed_count < 2:
            return "beginner"
        elif completed_count < 5:
            return "intermediate"
        else:
            return "advanced"
    
    def _get_stage_focus(self, stage):
        focus_map = {
            "beginner": "basic education and awareness building",
            "intermediate": "practical knowledge and comparisons",
            "advanced": "action items and product trials"
        }
        return focus_map.get(stage, "basic education")
    
    def _clean_json_response(self, response):
        match = re.search(r'```json(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def _get_default_quests_for_goal(self, goal_data):
        if "health" in goal_data['category'].lower():
            return [
                {
                    "id": f"quest_{goal_data['id']}_health_1",
                    "title": "Learn About Health Insurance",
                    "description": "Understand the basics of health insurance and its importance.",
                    "type": "learning",
                    "points": 100,
                    "difficulty": "Easy",
                    "estimated_time": "1-2 minutes",
                    "unlock_reward": "Health Insurance Guide",
                    "goal_id": goal_data['id'],
                    "learning_content": """# Health Insurance Basics

Health insurance is a contract between you and an insurance company that helps pay for medical expenses.

## Types of Coverage:
- **Hospital Insurance**: Covers hospital stays and treatments
- **Medical Insurance**: Covers doctor visits and outpatient care
- **Prescription Drug Coverage**: Covers medications
- **Specialist Care**: Covers specialist consultations

## Why It's Important:
- Protects against high medical costs
- Provides access to quality healthcare
- Offers peace of mind
- Required for financial security"""
                }
            ]
        elif "emergency" in goal_data['category'].lower():
            return [
                {
                    "id": f"quest_{goal_data['id']}_emergency_1",
                    "title": "Emergency Fund Basics",
                    "description": "Learn the importance of an emergency fund and why it's essential to have one.",
                    "type": "learning",
                    "points": 150,
                    "difficulty": "Easy",
                    "estimated_time": "1-2 minutes",
                    "unlock_reward": "Insight into emergency fund benefits",
                    "goal_id": goal_data['id'],
                    "learning_content": """# Emergency Fund Basics

An emergency fund is a savings buffer to cover unexpected expenses, providing financial stability during tough times.

## Why You Need an Emergency Fund:
- **Financial Security**: Protects against unexpected events like job loss or medical emergencies.
- **Avoid Debt**: Prevents reliance on credit cards or loans during crises.
- **Peace of Mind**: Reduces stress by ensuring you have funds available.

## How Much Should You Save?
- **Minimum**: 3 months of living expenses (e.g., rent, utilities, groceries).
- **Ideal**: 6 months of expenses for most people.
- **High-Risk Jobs**: Up to 12 months if your income is unstable (e.g., freelance or contract work).

## Where to Keep Your Emergency Fund:
- **High-Yield Savings Account**: Earns interest while keeping funds accessible.
- **Money Market Account**: Offers slightly higher returns with liquidity.
- **Avoid Risky Investments**: Keep funds safe and liquid, not in stocks or other volatile assets.

## Getting Started:
- Calculate your monthly expenses.
- Set a realistic savings goal (e.g., £500 to start).
- Automate monthly transfers to your savings account to build the fund over time."""
                }
            ]
        else:
            return [
                {
                    "id": f"quest_{goal_data['id']}_general_1",
                    "title": f"Introduction to {goal_data['category']}",
                    "description": f"Learn the basics of {goal_data['category']}.",
                    "type": "learning",
                    "points": 100,
                    "difficulty": "Easy",
                    "estimated_time": "1-2 minutes",
                    "unlock_reward": f"{goal_data['category']} Guide",
                    "goal_id": goal_data['id'],
                    "learning_content": f"{goal_data['category']} is an important aspect of financial planning."
                }
            ]

class NudgeAgent(AIAgentManager):
    def get_next_best_action(self, user_progress, persona_data, current_goal=None):
        goal_context = f"Current Goal: {current_goal['title']}" if current_goal else "No goal selected"
        messages = [
            {"role": "system", "content": f"""You are a Nudge Agent for Lloyds Bank's LifeQuest platform.
            Analyze user progress and provide personalized, motivating guidance.
            
            User: {persona_data['name']} ({persona_data['age']} years old, {persona_data['occupation']})
            {goal_context}
            
            Progress Analysis:
            - Total Points: {user_progress['total_points']}
            - Level: {user_progress['level']}
            - Completed Quests: {len(user_progress['completed_quests'])}
            - Unlocked Products: {len(user_progress['unlocked_products'])}
            
            Provide encouraging, specific guidance based on their progress and current goal.
            Focus on next actionable steps and benefits they'll gain.
            
            Return JSON:
            {{
                "message": "Personalized encouraging message",
                "action": "Specific next step they should take",
                "urgency": "High/Medium/Low",
                "reward_mention": "Specific points/rewards they can earn",
                "motivation": "Why this action is important for their goal"
            }}"""},
            {"role": "user", "content": "What should the user do next based on their progress?"}
        ]
        
        response = self.get_completion(messages, temperature=0.8)
        if response:
            try:
                response_clean = self._clean_json_response(response)
                return json.loads(response_clean)
            except json.JSONDecodeError:
                pass
        return {
            "message": f"Great progress, {persona_data['name']}! You're building strong financial habits.",
            "action": "Complete your next available quest to continue your journey",
            "urgency": "Medium",
            "reward_mention": "Earn 150+ LifePoints and unlock exclusive rewards!",
            "motivation": "Every quest completed brings you closer to your financial goals"
        }
    
    def _clean_json_response(self, response):
        match = re.search(r'```json(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

class RewardsAgent(AIAgentManager):
    def calculate_reward(self, quest_completed, user_level):
        base_points = quest_completed.get('points', 100)
        if base_points is None:
            base_points = 100
        multiplier = 1 + (user_level * 0.1)
        total_points = int(base_points * multiplier)
        unlock_rewards = []
        if total_points >= 200:
            unlock_rewards.append("Premium Financial Calculator")
        if total_points >= 400:
            unlock_rewards.append("30-Day Insurance Trial")
        if total_points >= 600:
            unlock_rewards.append("Personal Finance Consultation")
        return {
            "points_earned": total_points,
            "unlock_rewards": unlock_rewards,
            "achievement": self.get_achievement_badge(total_points)
        }
    
    def get_achievement_badge(self, total_points):
        if total_points >= 1000:
            return "🏆 Financial Champion"
        elif total_points >= 500:
            return "💎 Money Master"
        elif total_points >= 200:
            return "🌟 Smart Saver"
        else:
            return "🎯 Getting Started"

def initialize_session_state():
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = {
            'total_points': 0,
            'level': 1,
            'completed_quests': [],
            'current_goal': None,
            'achievements': [],
            'unlocked_products': []
        }
    if 'generated_goals' not in st.session_state:
        st.session_state.generated_goals = []
    if 'generated_quests' not in st.session_state:
        st.session_state.generated_quests = []
    if 'current_goal_id' not in st.session_state:
        st.session_state.current_goal_id = None
    if 'current_user_data' not in st.session_state:
        st.session_state.current_user_data = {}

def get_goal_popularity_percentage(category, age):
    # Simulated percentages for UK users pursuing each goal by age
    popularity_map = {
        "Health Insurance Coverage": 70 if age < 30 else 65,
        "Emergency Fund Building": 60 if age < 30 else 55,
        "Income Protection": 50 if age < 30 else 60,
        "Debt Management": 55 if age < 30 else 50,
        "Investment Planning": 45 if age < 30 else 65,
        "Retirement Planning": 30 if age < 30 else 70,
        "Life Insurance Coverage": 50 if age < 30 else 60,
        "Financial Education": 65 if age < 30 else 60
    }
    return popularity_map.get(category, 50)

def main():
    st.set_page_config(
        page_title="Lloyds LifeQuest",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_openai()
    initialize_session_state()
    
    # Initialize AI Agents
    goal_coach = GoalCoachAgent(st.session_state.openai_client)
    quest_agent = QuestAgent(st.session_state.openai_client)
    nudge_agent = NudgeAgent(st.session_state.openai_client)
    rewards_agent = RewardsAgent(st.session_state.openai_client)
    
    # Sidebar - User Profile Selection
    st.sidebar.title("🏦 Lloyds LifeQuest")
    st.sidebar.markdown("### Persona Selection")
    
    if st.session_state.current_user is None:
        selected_persona = st.sidebar.selectbox(
            "Select Profile:",
            list(PERSONAS_CONFIG.keys()),
            format_func=lambda x: f"{PERSONAS_CONFIG[x]['avatar']} {PERSONAS_CONFIG[x]['name']}"
        )
        # Input fields for persona attributes
        default_persona = PERSONAS_CONFIG[selected_persona]
        age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=default_persona['age'])
        st.sidebar.markdown("### Lifestyle Selection")
        occupation = st.sidebar.text_input("Occupation", value=default_persona['occupation'])
        income_range = st.sidebar.text_input("Income Range", value=default_persona['income_range'])
        current_products = st.sidebar.multiselect(
            "Current Products",
            options=AVAILABLE_PRODUCTS,
            default=default_persona['current_products']
        )
        if st.sidebar.button("Start Your Journey"):
            st.session_state.current_user = selected_persona
            st.session_state.current_user_data = {
                'name': default_persona['name'],
                'age': age,
                'occupation': occupation,
                'income_range': income_range,
                'current_products': current_products,
                'financial_status': default_persona['financial_status'],
                'risk_profile': default_persona['risk_profile'],
                'avatar': default_persona['avatar']
            }
            # Update PERSONAS_CONFIG with user inputs
            PERSONAS_CONFIG[selected_persona].update(st.session_state.current_user_data)
            st.rerun()
    else:
        persona = PERSONAS_CONFIG[st.session_state.current_user]
        st.sidebar.success(f"Welcome back, {persona['name']}!")
        st.sidebar.markdown("### Update Profile")
        age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=persona['age'])
        occupation = st.sidebar.text_input("Occupation", value=persona['occupation'])
        income_range = st.sidebar.text_input("Income Range", value=persona['income_range'])
        current_products = st.sidebar.multiselect(
            "Current Products",
            options=AVAILABLE_PRODUCTS,
            default=persona['current_products']
        )
        if st.sidebar.button("Update Profile"):
            st.session_state.current_user_data = {
                'name': persona['name'],
                'age': age,
                'occupation': occupation,
                'income_range': income_range,
                'current_products': current_products,
                'financial_status': persona['financial_status'],
                'risk_profile': persona['risk_profile'],
                'avatar': persona['avatar']
            }
            PERSONAS_CONFIG[st.session_state.current_user].update(st.session_state.current_user_data)
            st.success("Profile updated successfully!")
            st.rerun()
        st.sidebar.markdown("### Your Progress")
        st.sidebar.metric("Total Points", st.session_state.user_progress['total_points'])
        st.sidebar.metric("Level", st.session_state.user_progress['level'])
        st.sidebar.metric("Completed Quests", len(st.session_state.user_progress['completed_quests']))
        if st.session_state.user_progress['current_goal']:
            st.sidebar.markdown("### Current Goal")
            st.sidebar.info(f"🎯 {st.session_state.user_progress['current_goal']['title']}")
        if st.sidebar.button("Switch Profile"):
            st.session_state.current_user = None
            st.session_state.user_progress = {
                'total_points': 0,
                'level': 1,
                'completed_quests': [],
                'current_goal': None,
                'achievements': [],
                'unlocked_products': []
            }
            st.session_state.generated_goals = []
            st.session_state.generated_quests = []
            st.session_state.current_goal_id = None
            st.session_state.current_user_data = {}
            st.rerun()
    
    # Main Content
    if st.session_state.current_user is None:
        st.title("🌟 Welcome to Lloyds LifeQuest")
        st.markdown("""
        ### Your AI-Powered Protection & Wellness Journey
        
        **LifeQuest** uses advanced AI agents to create personalized protection goals, 
        engaging quests, and reward you for building better financial habits.
        
        #### Features:
        - 🎯 **AI Goal Coach**: Personalized financial goals based on your profile
        - 🎮 **Dynamic Quests**: AI-generated challenges tailored to your needs  
        - 🏆 **Smart Rewards**: Earn points and unlock exclusive products
        - 📈 **Real-time Progress**: Track your journey with live updates
        
        **Choose your profile from the sidebar to begin!**
        """)
    else:
        persona = PERSONAS_CONFIG[st.session_state.current_user]
        st.title(f"Hi {persona['name']}! 👋 Let’s Secure your life with LifeQuest")
        
        # Progress Bar
        progress_percentage = min(st.session_state.user_progress['total_points'] / 2000, 1.0)
        st.progress(progress_percentage)
        st.caption(f"Journey Progress: {int(progress_percentage * 100)}% Complete")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Goals", "🎮 Quests", "💡 AI Coach", "🏆 Rewards" ])
        
        with tab1:
            st.header("Your Insurance Protection Goals")
            st.success("89% of freelancers aged 25–35 in London opt for below income protection goals")
            if st.session_state.user_progress['current_goal']:
                current_goal = st.session_state.user_progress['current_goal']
                st.success(f"🎯 **Currently Selected Goal:** {current_goal['title']}")
                completed_quests = [q for q in st.session_state.generated_quests if q['id'] in st.session_state.user_progress['completed_quests'] and q['goal_id'] == current_goal['id']]
                total_quests = [q for q in st.session_state.generated_quests if q['goal_id'] == current_goal['id']]
                progress = (len(completed_quests) / max(len(total_quests), 1)) * 100
                st.progress(progress / 100)
                st.caption(f"Goal Progress: {progress:.1f}% ({len(completed_quests)}/{len(total_quests)} quests completed)")
                if st.button("🎮 Go to Quests", type="primary"):
                    st.session_state.tab = "quests"
                    st.rerun()
            if not st.session_state.generated_goals:
                if st.button("🤖 Generate Personalized Goals", type="primary"):
                    with st.spinner("AI Goal Coach is analyzing your profile..."):
                        goals = goal_coach.generate_personalized_goals(persona)
                        st.session_state.generated_goals = goals
                        st.rerun()
            else:
                st.success("✅ Goals generated by AI Goal Coach!")
                for goal in st.session_state.generated_goals:
                    is_selected = st.session_state.user_progress['current_goal'] and st.session_state.user_progress['current_goal']['id'] == goal['id']
                    with st.expander(f"🎯 {goal['title']} ({goal['priority']} Priority)" + (" - SELECTED" if is_selected else "")):
                        st.write(f"**Description:** {goal['description']}")
                        st.write(f"**Timeline:** {goal['timeline']}")
                        st.write(f"**Category:** {goal['category']}")
                        target_amount = goal.get('target_amount', 0)
                        st.write(f"**Target Amount:** £{target_amount:,}" if target_amount else "**Target Amount:** Not specified")
                        st.write(f"**Difficulty:** {goal['difficulty']}")
                        st.write(f"**Why Important:** {goal['why_important']}")
                        st.markdown(f"**{get_goal_popularity_percentage(goal['category'], persona['age'])}% of UK users your age are pursuing this goal**")
                        if not is_selected:
                            if st.button(f"Select This Goal", key=f"select_{goal['id']}"):
                                st.session_state.user_progress['current_goal'] = goal
                                st.session_state.generated_quests = []
                                st.success(f"Goal selected: {goal['title']}")
                                st.rerun()
                        else:
                            st.info("✅ This goal is currently selected")
        
        with tab2:
            st.header("Your Quests")
            if st.session_state.user_progress['current_goal']:
                current_goal = st.session_state.user_progress['current_goal']
                st.info(f"Current Goal: **{current_goal['title']}**")
                if not st.session_state.generated_quests:
                    if st.button("🤖 Generate Quests for This Goal", type="primary"):
                        with st.spinner("AI Quest Agent is creating your challenges..."):
                            quests = quest_agent.generate_quests_for_goal(current_goal, persona)
                            st.session_state.generated_quests = quests
                            st.rerun()
                else:
                    st.success("✅ Quests generated by AI Quest Agent!")
                    for quest in st.session_state.generated_quests:
                        if quest['goal_id'] != current_goal['id']:
                            continue
                        quest_id = quest['id']
                        is_completed = quest_id in st.session_state.user_progress['completed_quests']
                        status_icon = "✅" if is_completed else "🎯"
                        with st.expander(f"{status_icon} {quest['title']} ({quest.get('points', 100)} pts)"):
                            st.write(f"**Description:** {quest['description']}")
                            st.write(f"**Type:** {quest['type']}")
                            st.write(f"**Difficulty:** {quest['difficulty']}")
                            st.write(f"**Estimated Time:** {quest['estimated_time']}")
                            st.write(f"**Unlock Reward:** {quest['unlock_reward']}")
                            if not is_completed:
                                if quest['type'] == 'learning' and 'learning_content' in quest:
                                    st.markdown("### 📚 Learning Content")
                                    st.markdown(quest['learning_content'])
                                    st.markdown("---")
                                    if st.button(f"Mark as Completed", key=f"complete_{quest_id}"):
                                        st.session_state.user_progress['completed_quests'].append(quest_id)
                                        reward = rewards_agent.calculate_reward(quest, st.session_state.user_progress['level'])
                                        st.session_state.user_progress['total_points'] += reward['points_earned']
                                        if reward['unlock_rewards']:
                                            st.session_state.user_progress['unlocked_products'].extend(reward['unlock_rewards'])
                                        st.success(f"🎉 Quest completed! You earned {reward['points_earned']} points!")
                                        if reward['unlock_rewards']:
                                            st.success(f"🔓 Unlocked: {', '.join(reward['unlock_rewards'])}")
                                        if st.session_state.user_progress['total_points'] >= (st.session_state.user_progress['level'] * 500):
                                            st.session_state.user_progress['level'] += 1
                                            st.balloons()
                                        completed_count = len([q for q in st.session_state.user_progress['completed_quests'] if q.startswith(f"quest_{current_goal['id']}_")])
                                        if completed_count % 3 == 0:
                                            new_quests = quest_agent.generate_progressive_quests(current_goal, persona, completed_count)
                                            st.session_state.generated_quests.extend(new_quests)
                                            st.success(f"🆕 New quests unlocked!")
                                        st.rerun()
                                if quest['type'] == 'action' and 'action_steps' in quest:
                                    st.markdown("### 🎯 Action Steps")
                                    for i, step in enumerate(quest['action_steps'], 1):
                                        st.write(f"{i}. {step}")
                                    st.markdown("---")
                                    if st.button(f"Mark as Completed", key=f"complete_{quest_id}"):
                                        st.session_state.user_progress['completed_quests'].append(quest_id)
                                        reward = rewards_agent.calculate_reward(quest, st.session_state.user_progress['level'])
                                        st.session_state.user_progress['total_points'] += reward['points_earned']
                                        if reward['unlock_rewards']:
                                            st.session_state.user_progress['unlocked_products'].extend(reward['unlock_rewards'])
                                        st.success(f"🎉 Quest completed! You earned {reward['points_earned']} points!")
                                        if reward['unlock_rewards']:
                                            st.success(f"🔓 Unlocked: {', '.join(reward['unlock_rewards'])}")
                                        if st.session_state.user_progress['total_points'] >= (st.session_state.user_progress['level'] * 500):
                                            st.session_state.user_progress['level'] += 1
                                            st.balloons()
                                        completed_count = len([q for q in st.session_state.user_progress['completed_quests'] if q.startswith(f"quest_{current_goal['id']}_")])
                                        if completed_count % 3 == 0:
                                            new_quests = quest_agent.generate_progressive_quests(current_goal, persona, completed_count)
                                            st.session_state.generated_quests.extend(new_quests)
                                            st.success(f"🆕 New quests unlocked!")
                                        st.rerun()
                                if 'questions' in quest and quest['questions']:
                                    st.subheader("📝 Complete the Quiz:")
                                    user_answers = {}
                                    for i, q in enumerate(quest['questions']):
                                        st.write(f"**Question {i+1}:** {q['question']}")
                                        user_answer = st.radio(
                                            "Choose your answer:",
                                            q['options'],
                                            key=f"q_{quest_id}_{i}"
                                        )
                                        user_answers[i] = user_answer
                                    if st.button(f"Submit Quiz", key=f"submit_{quest_id}"):
                                        all_correct = True
                                        for i, q in enumerate(quest['questions']):
                                            correct_answer = q['options'][q['correct']]
                                            if user_answers[i] != correct_answer:
                                                all_correct = False
                                                st.error(f"Question {i+1}: Incorrect. {q['explanation']}")
                                            else:
                                                st.success(f"Question {i+1}: Correct! {q['explanation']}")
                                        if all_correct:
                                            st.session_state.user_progress['completed_quests'].append(quest_id)
                                            reward = rewards_agent.calculate_reward(quest, st.session_state.user_progress['level'])
                                            st.session_state.user_progress['total_points'] += reward['points_earned']
                                            if reward['unlock_rewards']:
                                                st.session_state.user_progress['unlocked_products'].extend(reward['unlock_rewards'])
                                            st.success(f"🎉 Quest completed! You earned {reward['points_earned']} points!")
                                            if reward['unlock_rewards']:
                                                st.success(f"🔓 Unlocked: {', '.join(reward['unlock_rewards'])}")
                                            if st.session_state.user_progress['total_points'] >= (st.session_state.user_progress['level'] * 500):
                                                st.session_state.user_progress['level'] += 1
                                                st.balloons()
                                            completed_count = len([q for q in st.session_state.user_progress['completed_quests'] if q.startswith(f"quest_{current_goal['id']}_")])
                                            if completed_count % 3 == 0:
                                                new_quests = quest_agent.generate_progressive_quests(current_goal, persona, completed_count)
                                                st.session_state.generated_quests.extend(new_quests)
                                                st.success(f"🆕 New quests unlocked!")
                                        st.rerun()
                            else:
                                st.success("✅ Quest completed!")
            else:
                st.info("👈 Select a goal first to unlock quests!")
        
        with tab4:
            st.header("Your Rewards & Achievements")
            st.markdown("**Points can be redeemed as a discount on processing fees for Lloyds Bank products.**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 LifePoints", st.session_state.user_progress['total_points'])
            with col2:
                st.metric("🏅 Level", st.session_state.user_progress['level'])
            with col3:
                completion_rate = (len(st.session_state.user_progress['completed_quests']) / max(len(st.session_state.generated_quests), 1)) * 100
                st.metric("📊 Completion Rate", f"{completion_rate:.1f}%")
            if st.session_state.user_progress['unlocked_products']:
                st.subheader("🔓 Unlocked Products & Trials")
                for product in st.session_state.user_progress['unlocked_products']:
                    st.success(f"✅ {product}")
                    st.success("**🏆You are rewarded with LifePoints and unlocks a simplified £50K critical illness cover for just £5/month**")
            total_points = st.session_state.user_progress['total_points']
            badge = rewards_agent.get_achievement_badge(total_points)
            st.subheader(f"🏆 Current Achievement: {badge}")
            st.subheader("🏆 Leaderboard")
            leaderboard_data = [
                {"name": "You", "points": st.session_state.user_progress['total_points']},
                {"name": "Alex M.", "points": random.randint(800, 1500)},
                {"name": "Sarah K.", "points": random.randint(600, 1200)},
                {"name": "Mike R.", "points": random.randint(400, 1000)},
                {"name": "Emma L.", "points": random.randint(200, 800)}
            ]
            leaderboard_data.sort(key=lambda x: x['points'], reverse=True)
            for i, user in enumerate(leaderboard_data):
                if user['name'] == "You":
                    st.success(f"#{i+1} 🏆 {user['name']}: {user['points']} points")
                else:
                    st.info(f"#{i+1} {user['name']}: {user['points']} points")
        
        with tab3:
            st.header("💡 AI Coach Recommendations")
            if st.button("🤖 Get Next Best Action", type="primary"):
                with st.spinner("AI Coach is analyzing your progress..."):
                    nudge = nudge_agent.get_next_best_action(st.session_state.user_progress, persona, st.session_state.user_progress['current_goal'])
                    st.success(f"💬 **Coach Says:** {nudge['message']}")
                    st.info(f"🎯 **Next Action:** {nudge['action']}")
                    st.warning(f"⚡ **Urgency:** {nudge['urgency']}")
                    st.warning("⚡ **Projected inflation is 4.2% — consider adjusting your coverage.**")
                    if nudge.get('reward_mention'):
                        st.success(f"🎁 **Reward:** {nudge['reward_mention']}")
            st.subheader("💬 Chat with Your AI Coach")
            user_question = st.text_input("Ask your AI Coach anything about your financial journey:")
            if user_question and st.button("Ask Coach"):
                messages = [
                    {"role": "system", "content": f"""You are a warm, intelligent, and friendly financial advisor for Lloyds Bank LifeQuest.

Your goal is to recommend **the best affordable health insurance plan** based on the user's income, lifestyle, and job pattern. 

The user is {persona['name']}, a {persona['age']}-year-old {persona['occupation']} with income range {persona['income_range']}.

Their current profile and financial goal:
{json.dumps(st.session_state.user_progress, indent=2)}

---

### 🔧 HOW TO RESPOND:
Give your response like a trusted coach who knows their life and wants to help.

Use the following structure and tone:

---

**🧭 Here's What I Recommend For You:**

Hi {persona['name']}, based on your income and freelance work pattern, here's a personalized health insurance suggestion to help you stay covered — without breaking your budget.

---

**💡 Recommended Plan:**
- ✅ **Plan Type**: Comprehensive cashless health cover  
- 💰 **Coverage Amount**: £50,000  
- 💸 **Estimated Monthly Premium**: £70–£90

This is a good balance between affordability and protection, especially for self-employed professionals like you.

---

**📊 Why This Fits Your Budget:**
With your income in the range of {persona['income_range']}, spending about **1.5–2% of your income** on health insurance is a smart choice.

That means:
- **Estimated Budget for Insurance**: £600–£900/year  
- Which equals about **£70–£90 per month**

This keeps your savings intact while still getting essential medical protection.

---

**🎯 Why This Plan Is Right For You:**
- You're a freelancer, so your income might vary — this plan offers **flexible premium options** and **cashless claims** to reduce stress during emergencies.
- It covers common medical expenses and hospitalization without the need for pre-approvals or long waiting periods.
- You don’t need to over-insure — this level of cover is enough to handle most medium-risk situations.

---

**⚠️ A Quick Heads-Up:**
Medical inflation is currently around **6.2%**. This means treatment costs can rise fast — so it’s better to **lock in a plan now** while premiums are low.

If your income grows in the next 6–12 months, you can upgrade your plan or add critical illness cover later.

---

**🎁 Bonus Tip:**
Securing this plan now may qualify you for **Lloyds Health Cashback** or other seasonal loyalty rewards.

---

Use plain, encouraging language. Make the user feel supported and confident.
Avoid robotic lists — speak like a person giving real, helpful advice.
                    """},
                    {"role": "user", "content": user_question}
                ]
                response = nudge_agent.get_completion(messages)
                if response:
                    st.success(f"🤖 **AI Coach:** {response}")

if __name__ == "__main__":
    main()