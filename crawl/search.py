import json

import httpx
from ddgs import DDGS


def search_with_serper(query: str, api_key: str) -> list:
    """Perform a search using Serper.dev API."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, data=payload, timeout=15.0)
            response.raise_for_status()
            results = response.json().get("organic", [])
            return [r.get("link") for r in results if r.get("link")]
    except Exception as e:
        print(f"Error searching with Serper for query '{query}': {e}")
        return []


def generate_target_urls(args, search_strategy):
    """Find target URLs using expanded query strategies via chosen search engine."""

    all_urls = {}
    print(f"Starting automated search for agricultural URLs using {args.search_engine.upper()}...")

    if args.search_engine == "serper" and not args.serper_api_key:
        raise ValueError("Serper API key is required when using the 'serper' search engine.")

    # DuckDuckGo logic
    if args.search_engine == "ddg":
        with DDGS() as ddgs:
            for label, queries in search_strategy.items():
                for query in queries:
                    print(f"--> Searching: {query}")
                    try:
                        results = ddgs.text(query, max_results=50)
                        for r in results:
                            url = r.get("href")
                            if url and url not in all_urls:
                                all_urls[url] = label
                    except Exception as e:
                        print(f"Error searching for {label} with query {query}: {e}")

    # Serper.dev logic
    elif args.search_engine == "serper":
        for label, queries in search_strategy.items():
            for query in queries:
                print(f"--> Searching: {query}")
                urls = search_with_serper(query, args.serper_api_key)
                for url in urls:
                    if url not in all_urls:
                        all_urls[url] = label

    print(f"\nSuccessfully found {len(all_urls)} unique URLs.")
    return all_urls
