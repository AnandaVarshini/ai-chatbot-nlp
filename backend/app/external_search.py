import requests
import re
import urllib.parse

try:
    from spellchecker import SpellChecker
    spell = SpellChecker()
    SPELL_AVAILABLE = True
except ImportError:
    SPELL_AVAILABLE = False
    print("pyspellchecker not installed")


class ExternalSearch:
    def __init__(self):
        self.headers = {
            "User-Agent": "AI-Study-Assistant/1.0"
        }
    
    # ============================================================
    # MAIN SEARCH
    # ============================================================
    def search(self, query):
        search_term = self._clean_query(query)
        print(f"Search: '{search_term}'")
        
        # STEP 1: Try ORIGINAL query first (no spell correction)
        result = self._search_internal(search_term)
        if result:
            print(f"✅ Found with original query")
            return result
        
        # STEP 2: Only spell-correct if original FAILED
        if SPELL_AVAILABLE:
            corrected = self._spell_correct(search_term)
            if corrected.lower() != search_term.lower():
                print(f"Spell-corrected: '{corrected}'")
                result = self._search_internal(corrected)
                if result:
                    return result
        
        # STEP 3: Last resort
        return self.generate_search_link(query)
    
    # ============================================================
    # INTERNAL SEARCH CHAIN (no spell correction inside)
    # ============================================================
    def _search_internal(self, search_term):
        # Try Wikipedia direct
        result = self._try_wikipedia_summary(search_term)
        if result:
            return result
        
        # Try Wikipedia opensearch
        result = self._wikipedia_opensearch(search_term)
        if result:
            return result
        
        # Try DuckDuckGo
        result = self.search_duckduckgo(search_term)
        if result:
            return result
        
        # Try Wikipedia full-text search
        result = self._wikipedia_search_api(search_term)
        if result:
            return result
        
        return None
    
    # ============================================================
    # SPELL CORRECTION (with proper noun protection)
    # ============================================================
    def _spell_correct(self, text):
        if not SPELL_AVAILABLE:
            return text
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            if len(word) < 3 or word.isdigit():
                corrected_words.append(word)
                continue
            
            if word.lower() in spell:
                corrected_words.append(word)
                continue
            
            correction = spell.correction(word.lower())
            
            if correction and correction != word.lower():
                candidates = spell.candidates(word.lower())
                original_capitalized = word[0].isupper() if word else False
                
                if len(correction) > len(word) + 2:
                    print(f"   Skipping '{word}' (name protection)")
                    corrected_words.append(word)
                    continue
                
                if len(words) == 2 and original_capitalized:
                    if abs(len(correction) - len(word)) <= 1:
                        diff_count = sum(1 for a, b in zip(word, correction) if a != b)
                        if diff_count <= 2:
                            print(f"   '{word}' -> '{correction}'")
                            corrected_words.append(correction)
                        else:
                            corrected_words.append(word)
                    else:
                        corrected_words.append(word)
                else:
                    print(f"   '{word}' -> '{correction}'")
                    corrected_words.append(correction)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words)
    
    # ============================================================
    # WIKIPEDIA STRATEGIES
    # ============================================================
    def _try_wikipedia_summary(self, search_term):
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(search_term)
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if (data.get("extract") 
                    and data.get("type") != "disambiguation" 
                    and len(data["extract"]) > 50):
                    return {
                        "source": "Wikipedia",
                        "title": data.get("title", ""),
                        "answer": data["extract"],
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    }
            return None
        except Exception as e:
            print(f"Wiki summary error: {e}")
            return None
    
    def _wikipedia_opensearch(self, search_term):
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": search_term,
                "limit": 5,
                "namespace": 0,
                "format": "json",
                "redirects": "resolve"
            }
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if len(data) >= 2 and data[1]:
                    suggestions = data[1]
                    print(f"Suggestions: {suggestions}")
                    for suggestion in suggestions[:3]:
                        result = self._try_wikipedia_summary(suggestion)
                        if result:
                            if suggestion.lower() != search_term.lower():
                                result["answer"] = "Did you mean: " + suggestion + "?\n\n" + result["answer"]
                            return result
            return None
        except Exception as e:
            print(f"Wiki opensearch error: {e}")
            return None
    
    def search_duckduckgo(self, query):
        try:
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("AbstractText") and len(data["AbstractText"]) > 50:
                    return {
                        "source": "DuckDuckGo",
                        "title": data.get("Heading", ""),
                        "answer": data["AbstractText"],
                        "url": data.get("AbstractURL", "")
                    }
                if data.get("Answer"):
                    return {
                        "source": "DuckDuckGo",
                        "title": query,
                        "answer": str(data["Answer"]),
                        "url": ""
                    }
                if data.get("Definition") and len(data["Definition"]) > 30:
                    return {
                        "source": "DuckDuckGo",
                        "title": data.get("Heading", ""),
                        "answer": data["Definition"],
                        "url": data.get("DefinitionURL", "")
                    }
            return None
        except Exception as e:
            print(f"DDG error: {e}")
            return None
    
    def _wikipedia_search_api(self, query):
        try:
            url = "https://en.wikipedia.org/w/api.php"
            # FIXED: Removed "srinfo": "suggestion" and added "srwhat": "text"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srwhat": "text", 
                "format": "json",
                "srlimit": 1,
                "srprop": "snippet"
            }
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get("query", {}).get("search", [])
                if results:
                    title = results[0]["title"]
                    print(f"Found exact page: {title}")
                    return self._try_wikipedia_summary(title)
            return None
        except Exception as e:
            print(f"Wiki search error: {e}")
            return None
    
    def generate_search_link(self, query):
        search_url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        return {
            "source": "Search",
            "title": query,
            "answer": "I couldn't find a complete answer. Read more here:\n\n" + search_url,
            "url": search_url
        }
    
    def _clean_query(self, query):
        q = query.lower().strip()
        
        prefixes = [
            "what is", "what are", "what's", "who is", "who was",
            "define", "meaning of", "explain", "tell me about",
            "how does", "how do", "why is", "why do",
            "when is", "when was", "where is", "where was",
            "can you explain", "give me", "show me", "what do you mean by",
            "what is a", "what is an", "what are the"
        ]
        prefixes.sort(key=len, reverse=True)
        for prefix in prefixes:
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
                break
                
        fillers = ["the", "a", "an", "of", "for", "in", "on", "at", "to", "with"]
        words = q.split()
        words = [w for w in words if w not in fillers]
        q = " ".join(words)
        
        q = q.rstrip("?.!").strip()
        return q if q else query