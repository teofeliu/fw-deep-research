import aiohttp
import xml.etree.ElementTree as ET
import urllib.parse

class WebSearcher:
    def __init__(self, config):
        self.config = config
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results = config.get("max_search_results", 10)
        
        # Define XML namespaces used in arXiv responses
        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
    
    async def search(self, query, num_results=None):
        """Search arXiv for papers matching the query."""
        results_count = num_results or self.max_results
        
        # Clean up the query for arXiv
        clean_query = self._clean_query_for_arxiv(query)
        print(f"    Cleaned arXiv query: {clean_query}")
        
        # Format the arXiv API URL
        params = {
            'search_query': f'all:{clean_query}',  # Search in all fields
            'start': 0,
            'max_results': results_count
        }
        
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        print(f"    Requesting: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    results = self._parse_arxiv_response(xml_data)
                    print(f"    Parsed {len(results)} results from arXiv response")
                    return results
                else:
                    error = await response.text()
                    raise Exception(f"arXiv search failed ({response.status}): {error}")
    
    def _parse_arxiv_response(self, xml_data):
        """Parse the arXiv API response XML into a list of paper data."""
        root = ET.fromstring(xml_data)
        results = []
        
        # Extract papers from the response
        for entry in root.findall('.//atom:entry', self.namespaces):
            paper = {
                'title': self._get_element_text(entry, './atom:title'),
                'authors': self._get_authors(entry),
                'summary': self._get_element_text(entry, './atom:summary'),
                'published': self._get_element_text(entry, './atom:published'),
                'updated': self._get_element_text(entry, './atom:updated'),
                'url': self._get_element_attr(entry, './atom:link[@title="pdf"]', 'href'),
                'id': self._get_element_text(entry, './atom:id'),
                'arxiv_id': self._extract_arxiv_id(
                    self._get_element_text(entry, './atom:id')
                ),
                'comment': self._get_element_text(entry, './arxiv:comment'),
                'journal_ref': self._get_element_text(entry, './arxiv:journal_ref'),
                'categories': self._get_categories(entry)
            }
            results.append(paper)
        
        return results
    
    async def fetch_content(self, paper):
        """
        For arXiv, we already have the content (summary/abstract) from the search.
        This just reformats it to match our expected structure.
        """
        return {
            'url': paper['url'],
            'title': paper['title'],
            'content': f"Abstract: {paper['summary']}\n\nAuthors: {', '.join(paper['authors'])}\n\nPublished: {paper['published']}\n\nCategories: {', '.join(paper['categories'])}\n\nID: {paper['arxiv_id']}",
            'summary': paper['summary']
        }
    
    def _get_element_text(self, element, xpath):
        """Get the text content of an XML element."""
        el = element.find(xpath, self.namespaces)
        return el.text.strip() if el is not None and el.text else ""
    
    def _get_element_attr(self, element, xpath, attr):
        """Get an attribute from an XML element."""
        el = element.find(xpath, self.namespaces)
        return el.get(attr, "") if el is not None else ""
    
    def _get_authors(self, entry):
        """Extract all authors from an entry."""
        authors = []
        for author in entry.findall('./atom:author', self.namespaces):
            name = author.find('./atom:name', self.namespaces)
            if name is not None and name.text:
                authors.append(name.text.strip())
        return authors
    
    def _get_categories(self, entry):
        """Extract all categories from an entry."""
        categories = []
        for category in entry.findall('./atom:category', self.namespaces):
            term = category.get('term')
            if term:
                categories.append(term)
        return categories
    
    def _extract_arxiv_id(self, id_url):
        """Extract the arXiv ID from the full URL."""
        if id_url:
            # URLs are typically like http://arxiv.org/abs/2107.12345
            parts = id_url.split('/')
            return parts[-1] if parts else id_url
        return ""
    
    def _clean_query_for_arxiv(self, query):
        """Clean and format a query for arXiv search."""
        # Remove special markdown formatting
        clean = query.replace("**", "").replace("*", "")
        
        # Remove any explanatory text after colons
        if ":" in clean and len(clean.split(":")[0].split()) < 5:
            clean = clean.split(":", 1)[1].strip()
        
        # Remove other noise that might be in the query
        noise_phrases = [
            "A search query focusing on this could be",
            "A relevant search query might be",
            "A search query for this could be"
        ]
        
        for phrase in noise_phrases:
            if phrase in clean:
                clean = clean.replace(phrase, "").strip()
        
        # Truncate if too long
        words = clean.split()
        if len(words) > 10:
            clean = " ".join(words[:10])
        
        return clean