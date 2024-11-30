from Agent import CreateAllAgents
from camel.tasks import Task
from camel.workforce import Workforce
from configs import NAMES, ROLES, PROJECT, DETAILS, PDF_PATH, extract_text_form_pdf, COLORS, extract_text_with_images_from_pdf, Badges_CSS, Badges_HTML, TITLE_HTML, AGENTS_RESPONSE_SECTION_TITLE, INPUT_SECTION_TITLE, METRICS_TITLE, RESULTS_DIR
import gradio as gr
import markdown
from weasyprint import HTML
from nlp_metrics import evaluate_documents_nlp



def CreateFirstTask(question_id):
    team = []
    for name, role in zip(NAMES, ROLES):
        team.append(f"{name} {role}")
    task_content = f"""
    Consider yourself as a Senior Design Project Co-pilot designed to give constructive criticism, valueable feedback, and overall score to the proposal, to the engineering students doing the project. 
    You are tasked with evaluation of a Senior Design Project proposal titled: '{PROJECT}'. 
    The following are the details of the project provided by the students: {DETAILS}.
    
    Your role is to coordinate a team of experts, breaking down the feedback process into smaller, focused tasks. 
    The team working on the project is: {str(team)}.

    Each expert should evaluate specific elements of the proposal according to their expertise and provide a final score out of 5, Strengths, Weaknesses and Suggestions. that will help the students. 
    They need to provide detailed feedback on the feasibility, strengths, and areas where the proposed solution could be improved. 

    Based on their output, return the output in exact format as:
        Overall Score: X/5 (This score can be calculated by taking the average of score given by each agent)
        Detailed Comprehensive Feedback:
        In addition to the numerical scores, you should also provide:
        1. Strengths: Highlight areas where the project excels, emphasizing strong alignment with complex engineering problem-solving criteria (based on the outputs of all the agents).
        2. Weaknesses: Identify any gaps or shortcomings in the problem formulation, methodology, or other relevant aspects that detract from the project’s effectiveness in addressing complexity (based on the outputs of all the agents).
        3. Suggestions for Improvement: Offer actionable advice to enhance the project’s approach, such as refining the problem formulation, considering additional interdisciplinary aspects, or improving ethical considerations (based on the outputs of all the agents).

    Sample Output (Just for formatting purposes):
        Project Title: XXX

        Overall Score: 4.2 (Average Score Across All Agents)

        Evaluation Summary:
        The project proposal is well-formulated and demonstrates a strong approach to tackling a complex engineering problem. It is particularly strong in [highlight top strengths], but there are areas for improvement in [highlight key weaknesses].

        Detailed Scores and Feedback by Criterion:

        1. Problem Scope and Depth
        - Score: 4
        - Strengths: Clear articulation of problem scope; strong interdisciplinary focus.
        - Weaknesses: Lacks detailed analysis of specialized techniques.
        - Suggestions: Include more background research and specify challenges related to interdisciplinarity.

        2. Uncertainty and Ambiguity**
        - Score: 3
        - Strengths: Acknowledges some uncertainties in data availability.
        - Weaknesses: Needs further exploration of assumptions and potential data gaps.
        - Suggestions: Develop a strategy for addressing ambiguity in the data.
	    And so on for the other agents as well...

	Overall Comments: The project is well-aligned with complex engineering problem-solving requirements but would benefit from [summary of key suggestions].
    """

    return Task(content=task_content, additional_info=DETAILS, id=str(question_id))

def CreateWorkForce(PROJECT, DETAILS):
    Agents = CreateAllAgents(PROJECT, DETAILS)
    workforce = Workforce(
        description="Engineering Project Proposal Critic Team",
    )
    for Role, (Name, Agent) in zip(ROLES, zip(NAMES, Agents)):
        workforce.add_single_agent_worker(Name+" Role: "+Role, worker=Agent)
    
    return workforce

def Followup_tasks(followup_question, question_id, summary, subtasks):
    task_content = f"""In the previous iteration, you and your team of experts provided feedback on the Senior Design Project proposal titled: '{PROJECT}'.
    Summary of Last Feedback: {summary}
    The students have now submitted a follow-up question or task based on the feedback they received: "{followup_question}.
    Your task is to offer additional feedback, constructive criticism, and suggestions addressing this follow-up. Based on the nature of the question or task, determine which agents are best suited to respond, assign responsibilities accordingly, and decide if any agents may not be needed for this iteration.
    You are not required to use all the agents again, but you may need to consult with some of them to provide a comprehensive response to the students so, choose the agents according to the followup question.
    """
    return Task(content=task_content, additional_info= f'''Detailed Last Feedback from Each Expert: {subtasks}''', id=str(question_id))


PDF_PATH = ""
PROJECT = ""
summarized_result = ""
summary_history = []
subtasks_history = []
question_id = 0
followup_questions = []
start = True
workForce = CreateWorkForce(PROJECT, DETAILS)

def NLP_Metrics_calculation(pdf_file):
    document = extract_text_with_images_from_pdf(pdf_file)
    NLP_Metrics = evaluate_documents_nlp(document)
    return NLP_Metrics, document

def Process_SDP_Proposal(title, pdf_file, document, badge_html):
    global start, question_id, PROJECT, DETAILS, PDF_PATH
    start = True
    question_id = 0
    PDF_PATH = pdf_file
    PROJECT = title
    DETAILS = document
    task = CreateFirstTask(question_id)
    start = False

    # Process the task with agents
    result = workForce.process_task(task)

    
    # Store results from each subtask and summary
    subtasks_results = {ROLES[i]: subtask.result for i, subtask in enumerate(result.subtasks)}
    summarized_result = result.result
    subtasks_history.append(subtasks_results)
    summary_history.append(summarized_result)
    agent_responses_html = ""
    # Format agent responses in HTML with markdown-like styling
    for role, response in subtasks_results.items():
        color = COLORS[role]
        agent_responses_html += f"""
        <div style='background-color:{color}; padding: 15px; margin: 5px 0; border-radius: 5px;' markdown=1>
            {markdown.markdown(f"#Agent: {role}<br> {response}", extensions=['extra', 'codehilite', 'toc', 'sane_lists', 'smarty', 'admonition', 'attr_list', 'footnotes', 'nl2br', 'wikilinks', "meta"])}
        </div>
        """
    summary_block = f"""
    <div style='background-color:#4c4852; padding: 15px; margin: 5px 0; border-radius: 5px;' markdown=1>
            {markdown.markdown(summarized_result, extensions=['extra', 'codehilite', 'toc', 'sane_lists', 'smarty', 'admonition', 'attr_list', 'footnotes', 'nl2br', 'wikilinks', "meta"])}
        </div>
        """
    HTML(string=summary_block + agent_responses_html + badge_html).write_pdf(f"{RESULTS_DIR}/{title}.pdf")
    result_string = f"""Title and PDF received. Initial feedback provided by agents."""

    return result_string, gr.update(visible=True), agent_responses_html, summary_block

# Function to handle follow-up messages
def agent_conversation(user_message):
    global question_id
    
    followup_questions.append(user_message)
    task = Followup_tasks(followup_questions[-1], question_id, summary_history[-1], subtasks_history[-1])
    result = workForce.process_task(task)
    
    # Update history with the new response from agents
    subtasks_results = {ROLES[i]: subtask.result for i, subtask in enumerate(result.subtasks)}
    subtasks_history.append(subtasks_results)
    summary_history.append(result.result)
    
    # Format agent responses in HTML
    messages = ""
    for role, response in subtasks_results.items():
        color = COLORS[role]
        messages += f"""
        <div style='background-color:{color};  padding: 15px; margin: 5px 0; border-radius: 5px;' markdown=1>
            {markdown.markdown(f"#Agent: {role}<br>{response}", extensions=['extra','codehilite', 'toc', 'sane_lists', 'smarty', 'admonition', 'attr_list', 'footnotes', 'nl2br', 'wikilinks', "meta"])}
        </div>
        """
    summary_block = f"""
    <div style='background-color:#4c4852;  padding: 15px; margin: 5px 0; border-radius: 5px;' markdown=1>
            {markdown.markdown(result.result, extensions=['extra','codehilite', 'toc', 'sane_lists', 'smarty', 'admonition', 'attr_list', 'footnotes', 'nl2br', 'wikilinks', "meta"])}
        </div>
        """
    question_id += 1
    return messages, summary_block

with gr.Blocks(css=Badges_CSS) as interface:
    title = gr.HTML(f"""
                    {TITLE_HTML}
                    """)
    with gr.Row():
        with gr.Column(scale=1):  # Left column for inputs, and NLP-based Metrics
            gr.HTML(f"{INPUT_SECTION_TITLE}")
            title = gr.Textbox(label="Enter Title")
            pdf_file = gr.File(label="Upload Proposal PDF", file_types=['.pdf'])
            result = gr.Textbox(label="Result",value="Once submitted, ~300-600 seconds will be required (depending upon the number of pages) to process entire PDF by the agents.", interactive=False)
            submit = gr.Button("Submit")
            user_message = gr.Textbox(label="Followup Message", placeholder="Ask Follow-up Questions After Initial Feedback from Agents", visible=False)
            send_message = gr.Button("Send Message", visible=False)
            
        with gr.Column(scale=2):  # Right column for outputs
            gr.HTML(f"""{AGENTS_RESPONSE_SECTION_TITLE}""")
            gr.Markdown("# Summarized Output")
            summary_response_block = gr.HTML()
            gr.HTML("""<hr>""")
            gr.Markdown("# Agent-Wise Responses")
            agent_response_blocks = gr.HTML()
        with gr.Column(scale = 0.5):
            gr.HTML(f"{METRICS_TITLE}")
            #gr.Markdown("# NLP-based Metrics")
            gr.Markdown("## Calculated using the Submitted Proposal")
            gr.Markdown("These are derived form the submitted proposals. Scores from Agents will be displayed in the middle section.")
            badge_container = gr.HTML(value=f"""
                {Badges_HTML.format(
                lexical_cohesion_score="N/A",
                avg_sentence_length_score="N/A",
                clause_density_score="N/A",
                flesch_kincaid_score="N/A"
                )}
            """)
    def on_submit(title, pdf_file):
        nlp_metrics, document = NLP_Metrics_calculation(pdf_file)
        print(f"MLP-based metrics from the submitted proposal PDF: {nlp_metrics}")
        badge_html = f"""
            {
                Badges_HTML.format(
                lexical_cohesion_score= nlp_metrics.get("Lexical Cohesion", "N/A"),
                avg_sentence_length_score= nlp_metrics.get("Average Sentence Length", "N/A"),
                clause_density_score= nlp_metrics.get("Clause Density", "N/A"),
                flesch_kincaid_score= nlp_metrics.get("Flesch-Kincaid", "N/A"))
            }
        """
        result_text, section_visible, agent_response_html, summary_block= Process_SDP_Proposal(title, pdf_file, document, badge_html)
        return result_text, agent_response_html, summary_block, section_visible, section_visible, gr.update(value=badge_html)

    submit.click(on_submit, inputs=[title, pdf_file], outputs=[result, agent_response_blocks, summary_response_block, user_message, send_message, badge_container])
    send_message.click(agent_conversation, inputs=user_message, outputs= [agent_response_blocks, summary_response_block])


interface.launch()