import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from firecrawl import FirecrawlApp

# ANSI color codes
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Load environment variables
load_dotenv()

class FireCrawl:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FireCrawl, cls).__new__(cls)
            cls._instance.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com"
                )
            cls._instance.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
            cls._instance.app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        return cls._instance

    def search_google(self, query):
        """Search Google using SerpAPI and return top results."""
        print(f"{Colors.YELLOW}Searching Google for '{query}'...{Colors.RESET}")
        search = GoogleSearch({"q": query, "api_key": os.getenv("SERP_API_KEY")})
        return search.get_dict().get("organic_results", [])

    def select_urls_with_r1(self, serp_results):
        """
        Use R1 to select the most relevant URLs from SERP results objective.
        Returns a JSON object with a "selected_urls" property that is an array of strings.
        """
        try:
            # Prepare the data for R1
            serp_data = [{"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")} 
                        for r in serp_results if r.get("link")]
            print(f"{Colors.GREEN}Using R1 to gather urls...{Colors.RESET}")

            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {
                        "role": "system",
                        "content": "Identify URLs that are **curated lists/collections of food reviews**\
                              (e.g., 'Top 10 Restaurants in X,' 'Best Dishes of 2024')."
                    },
                    {
                        "role": "user",
                        "content": ("""**Objective**: Find URLs that are **collections/roundups of food reviews** (e.g., ranked lists, aggregated guides).  
                                    **Avoid**: Single-restaurant reviews, recipe blogs, or social media links.
                                    **SERP Examples**:
                                    **Good**: 
                                    - Title: "Top 50 Restaurants in Paris 2024 | Food Magazine" 
                                    - Snippet: "Our annual ranked list of the finest dining spots." 
                                    - URL: `https://foodmag.com/best-paris-restaurants` → **Include as-is** 
                                    - Title: "Best Pizza in NYC"   
                                    - Snippet:"A curated guide to 20 iconic pizzerias." 
                                    - URL: `https://foodmag.com` → **Add /*** (if the list isn’t on the homepage) 
                                     **Bad**: 
                                    - Title: "10 Easy Pasta Recipes" 
                                    - URL: `https://recipes.com/pasta` → **Exclude** (not a review collection) 
                                    **SERP Results**: 
                                    {json.dumps(serp_data, indent=2)}
                                    Return a JSON object with **only** valid collections under `selected_urls`:
                                    """
                                    )
                    }
                ],
            )

            result = json.loads(response.choices[0].message.content)
            urls = result.get("selected_urls", [])
            return urls

        except Exception as e:
            print(f"{Colors.RED}Error selecting URLs with R1: {e}{Colors.RESET}")
            return []

    def extract_info(self, urls, prompt):
        """Use requests to call Firecrawl's extract endpoint with selected URLs."""
        print(f"{Colors.YELLOW}Extracting structured data from the provided URLs using Firecrawl's /extract endpoint...{Colors.RESET}")
        try:
            response = self.app.extract(urls, {"prompt": prompt, "enableWebSearch": True})
            print(response)
            return response
        except Exception as e:
            print(f"{Colors.RED}Failed to extract data: {e}{Colors.RESET}")
            return None
    
    def pull_collections(self, query):
        serp_results = self.search_google(query)
        urls = self.select_urls_with_r1(serp_results)
        return urls

    def deduplicate_with_r1(self, data, company, objective):
        """Use R1 to deduplicate and consolidate extracted information."""
        print(f"{Colors.YELLOW}Deduplicating and consolidating information using R1...{Colors.RESET}")
        
        try:
            # Ensure data is valid JSON before sending
            if not data:
                return {}
                
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at consolidating information and removing duplicates. Analyze the extracted data and provide a clean, consolidated response."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Company: {company}\n"
                            f"Objective: {objective}\n"
                            f"Extracted Data: {json.dumps(data, indent=2)}\n\n"
                            "Please analyze this data and:\n"
                            "1. Remove any duplicate information\n"
                            "2. Consolidate similar points\n"
                            "3. Format the response as a clean JSON object\n"
                            "4. Ensure all information is relevant to the objective\n"
                            "Return only the JSON response."
                        )
                    }
                ],
            )
            
            # Handle empty or invalid responses
            response_text = response.choices[0].message.content.strip()
            if not response_text:
                return {}
                
            try:
                consolidated_data = json.loads(response_text)
                return consolidated_data
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the response
                # Look for content between curly braces
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start >= 0 and end >= 0:
                    json_str = response_text[start:end+1]
                    return json.loads(json_str)
                return {}
            
        except Exception as e:
            print(f"{Colors.RED}Error deduplicating data with R1: {e}{Colors.RESET}")
            return data
        
    
    # def crawl(self, query, init_objective, final_objective):
    #     serp_results = self.search_google(query)
    #     # urls = self.select_urls_with_r1(init_objective, serp_results)
    #     data = self.extract_info(['https://sandiego.eater.com/neighborhood/1526/la-jolla'], final_objective)
    #     return self.deduplicate_with_r1(data, query, final_objective)
