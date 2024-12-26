import os
import sys
import logging
from github import Github
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
import time

class LLMAnalyzer:
    def __init__(self):
        print("\nInitializing Ollama model...")
        with tqdm(total=1, desc="Loading model") as pbar:
            self.model = OllamaLLM(
                model="codellama",
                temperature=0.7,
                timeout=30  # Add timeout
            )
            pbar.update(1)
        self._setup_prompt_template()

    def _setup_prompt_template(self):
        self.prompt_template = PromptTemplate(
            input_variables=["workflow_name", "status", "conclusion"],
            template="""
            Analyze CI/CD workflow status - provide concise analysis:
            Name: {workflow_name}
            Status: {status}
            Result: {conclusion}

            Quick Analysis:
            1. Status: [Success/Failure]
            2. Issues: [Critical/Minor/None]
            3. Actions: [Required steps]
            4. Fixes: [Recommendations]
            """
        )

    def analyze_workflow(self, workflow: Dict) -> str:
        try:
            start_time = time.time()
            with tqdm(total=1, desc=f"Analyzing {workflow['name']}") as pbar:
                prompt = self.prompt_template.format(
                    workflow_name=workflow.get('name', 'Unknown'),
                    status=workflow.get('status', 'Unknown'),
                    conclusion=workflow.get('conclusion', 'Unknown')
                )
                result = self.model.invoke(prompt)
                pbar.update(1)
            
            elapsed = time.time() - start_time
            return f"{result}\nAnalysis completed in {elapsed:.2f}s"
        except Exception as e:
            return f"Analysis Error: {str(e)}"

class GithubCICDAgent:
    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("Missing GITHUB_TOKEN environment variable")
        self.github = Github(self.github_token)
        self.analyzer = LLMAnalyzer()

    def monitor_workflow_runs(self, repo_name: str) -> List[Dict]:
        repo = self.github.get_repo(repo_name)
        workflows = repo.get_workflow_runs()
        return [{
            "name": w.name,
            "status": w.status,
            "conclusion": w.conclusion,
            "url": w.html_url
        } for w in workflows]

    def analyze_workflows(self, workflows: List[Dict]) -> List[Dict]:
        return [{
            **w,
            "analysis": self.analyzer.analyze_workflow(w)
        } for w in workflows]

def main():
    try:
        agent = GithubCICDAgent()
        repo_name = input("Enter repository name (format: owner/repo): ")
        
        print("\nAnalyzing workflows...")
        workflows = agent.monitor_workflow_runs(repo_name)
        
        if workflows:
            analyzed = agent.analyze_workflows(workflows)
            print("\nWorkflow Analysis:")
            for w in analyzed:
                print(f"\n{'-'*50}")
                print(f"Workflow: {w['name']}")
                print(f"Status: {w['status']}")
                print(f"Conclusion: {w['conclusion']}")
                print(f"Analysis:\n{w['analysis']}")
                print(f"URL: {w['url']}")
        else:
            print("No workflows found or error occurred")
            
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()