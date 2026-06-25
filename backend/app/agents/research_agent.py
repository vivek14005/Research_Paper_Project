from typing import Annotated, List, TypedDict, Dict, Any, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from app.config import settings
from app.rag.vector_store import vector_manager
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    paper_ids: List[str]
    context: str
    summary_type: str # basic, technical, deep
    next_agent: str
    analysis_results: Dict[str, Any]

class ResearchAgents:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", openai_api_key=settings.OPENAI_API_KEY)
        self.builder = StateGraph(AgentState)
        self._setup_graph()

    def _setup_graph(self):
        self.builder.add_node("retriever", self.retriever_node)
        self.builder.add_node("analyzer", self.analyzer_agent)
        self.builder.add_node("summarizer", self.summarizer_agent)
        self.builder.add_node("chat", self.chat_agent)
        self.builder.add_node("supervisor", self.supervisor_node)

        self.builder.set_entry_point("supervisor")
        
        self.builder.add_conditional_edges(
            "supervisor",
            lambda x: x["next_agent"],
            {
                "retriever": "retriever",
                "analyzer": "analyzer",
                "summarizer": "summarizer",
                "chat": "chat",
                "end": END
            }
        )

        self.builder.add_edge("retriever", "supervisor")
        self.builder.add_edge("analyzer", "supervisor")
        self.builder.add_edge("summarizer", "supervisor")
        self.builder.add_edge("chat", "supervisor")

        self.graph = self.builder.compile()

    async def supervisor_node(self, state: AgentState):
        last_message = state["messages"][-1].content.lower()
        
        # If we don't have context yet, we must retrieve it
        if not state.get("context"):
            return {"next_agent": "retriever"}

        if "summarize" in last_message or "summary" in last_message:
            return {"next_agent": "summarizer"}
        elif "analyze" in last_message or "extraction" in last_message:
            return {"next_agent": "analyzer"}
        elif "?" in last_message or len(state["messages"]) > 1:
            return {"next_agent": "chat"}
        else:
            return {"next_agent": "end"}

    async def retriever_node(self, state: AgentState):
        query = state["messages"][-1].content
        retriever = vector_manager.get_retriever(paper_ids=state["paper_ids"])
        docs = await retriever.ainvoke(query)
        context = "\n\n".join([f"Page {d.metadata.get('page')}: {d.page_content}" for d in docs])
        return {"context": context}

    async def analyzer_agent(self, state: AgentState):
        prompt = f"""
        Analyze the following research context and extract key contributions, methodology, and limitations.
        You MUST only use the provided context.
        If information is missing, state 'Information not found in uploaded research papers.'
        Always cite the Page Number using [Page X] format.
        
        Context: {state['context']}
        """
        response = await self.llm.ainvoke(prompt)
        return {"messages": [response]}

    async def summarizer_agent(self, state: AgentState):
        prompt = f"""
        Generate a {state.get('summary_type', 'technical')} summary for the paper context.
        Explain the paper clearly. Avoid general knowledge.
        Always cite sources using [Page X].
        
        Context: {state['context']}
        """
        response = await self.llm.ainvoke(prompt)
        return {"messages": [response]}

    async def chat_agent(self, state: AgentState):
        prompt = f"""
        Act as an expert Research Assistant. 
        Answer the following question using ONLY the provided context.
        
        RULES:
        1. If the answer is not in the context, say "Information not found in uploaded research papers."
        2. ALWAYS cite the Page Number like [Page X].
        3. If possible, mention the Section name.
        4. Be precise and academic.
        
        Question: {state['messages'][-1].content}
        
        Context: {state['context']}
        """
        response = await self.llm.ainvoke(prompt)
        return {"messages": [response]}

research_agent_system = ResearchAgents()
