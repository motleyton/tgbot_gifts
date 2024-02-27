from langchain.tools import BaseTool
import re
from googleapiclient.discovery import build
from typing import List, Any

class GoogleSearchTool():
    name = "Google Search Tool"
    description = "Performs searches on Google Custom Search Engine and returns results."

    def __init__(self, config: dict):
        self.config = config
        self.google_api_key = config['google_api_key']
        self.google_cse_id = config['google_cse_id']

    def google_search(self, search_term: str, **kwargs) -> List[str]:
        service = build("customsearch", "v1", developerKey=self.google_api_key)
        res = service.cse().list(q=search_term, cx=self.google_cse_id, **kwargs).execute()
        return res.get('items', [])


    def parse_gpt_response(self, response_text: str) -> List[str]:
        lines = response_text.split('\n')
        search_queries = []
        for line in lines:
            match = re.match(r'^\d+\.\s*([^:]+)', line)
            if match:
                search_queries.append(match.group(1))
        return search_queries