#!/usr/bin/env python3
"""
Multi-source ServiceNow Jobs Orchestrator
- Loads all scrapers from scrapers directory
- Runs them in parallel
- Aggregates and deduplicates results
- Saves to JSON for processing
"""

import importlib.util
import os
from datetime import datetime
from pathlib import Path
from job_model import Job

SCRAPERS_DIR = Path(__file__).parent / "scrapers"
OUTPUT_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "all_jobs.json"

def load_scraper(name: str):
    """Load a scraper module dynamically"""
    scraper_file = SCRAPERS_DIR / f"{name}_scraper.py"
    if not scraper_file.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(name, scraper_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"[Orchestrator] Error loading {name}: {e}")
        return None

def run_all_scrapers():
    """Run all scrapers from the scrapers directory"""
    all_jobs = []
    seen_sources = set()
    
    # List all potential scraper files
    for file in SCRAPERS_DIR.glob("*.py"):
        if file.name == "__pycache__":
            continue
            
        # Extract source name (e.g., "hunt_uk_scraper.py" -> "hunt_uk")
        source_name = file.stem.replace("_scraper", "")
        if not source_name or source_name.startswith('_'):
            continue
        
        print(f"\n[Orchestrator] Loading scraper for {source_name}...")
        module = load_scraper(source_name)
        if module:
            try:
                # Try to get the scrape function
                if hasattr(module, 'scrape'):
                    jobs = module.scrape()
                    if jobs:
                        print(f"[Orchestrator] {source_name}: {len(jobs)} jobs")
                        all_jobs.extend(jobs)
                        seen_sources.add(source_name)
            except Exception as e:
                print(f"[Orchestrator] Error running {source_name}: {e}")
    
    print(f"\n[Orchestrator] Total sources loaded: {len(seen_sources)}")
    return all_jobs

def deduplicate_jobs(jobs: list[Job]) -> list[Job]:
    """Remove duplicate jobs based on link or hash"""
    unique_jobs = []
    seen = set()
    
    for job in jobs:
        # Use link if available, otherwise use hash
        identifier = job.link if job.link else job.hash
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_jobs.append(job)
    
    return unique_jobs

def save_jobs(jobs: list[Job], path: Path):
    """Save jobs to JSON file"""
    import json
    data = [job.to_dict() for job in jobs]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[Orchestrator] Saved {len(jobs)} jobs to {path}")

def main():
    print("=" * 60)
    print("MULTI-SOURCE JOB SCRAPER ORCHESTRATOR")
    print("=" * 60)
    
    # Run all scrapers
    jobs = run_all_scrapers()
    
    if not jobs:
        print("[Orchestrator] No jobs found from any source!")
        return
    
    # Deduplicate
    unique_jobs = deduplicate_jobs(jobs)
    print(f"\n[Orchestrator] Total unique jobs: {len(unique_jobs)}")
    
    # Save to JSON
    save_jobs(unique_jobs, OUTPUT_FILE)
    
    print(f"\n[Orchestrator] Scrape completed successfully!")
    print(f"Total unique ServiceNow jobs found: {len(unique_jobs)}")

if __name__ == "__main__":
    main()