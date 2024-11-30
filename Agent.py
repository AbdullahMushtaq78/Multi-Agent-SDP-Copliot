from configs import *

def MakeAgent(Name:str, Role:str, Project:str,Details:str):
    persona = PERSONAS[Role]
    
    base_msg = textwrap.dedent(
        f"""        
        Here is your persona that you must act with: {persona}.
        
        Title of the Senior Design Project Proposal: '{Project}'. 
        
        The following are the details of the project proposal: {Details}.
        
        """
    )
    model_configs = ChatGPTConfig(
        temperature=TEMPERATURE,
        tools = TOOLS[Name]
    )
    model = ModelFactory.create(
            model_platform=PLATFORM,
            model_type=MODEL,   
            model_config_dict=model_configs.as_dict()
        )
    agent = CriticAgent(BaseMessage.make_assistant_message(role_name=Role, content=base_msg), model=model, message_window_size=10)
    agent.reset()
    return agent

def CreateAllAgents(project, details):
    Agents = [MakeAgent(name, role, project, details) for name, role in zip(NAMES, ROLES)]
    return Agents

