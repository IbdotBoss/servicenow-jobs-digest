#!/usr/bin/env python3
import asyncio
"""Multi-source ServiceNow Jobs Orchestrator"""

import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
from datetime import datetime
from pathlib import Path
from job_model import Job

SCRAPERS_DIR = Path(__file__).parent / "scrapers"
OUTPUT_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest" / "docs" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "jobs.json"

def load_scraper(name: str):
    """Load a scraper module"""
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

def run_scraper(module, name: str):
    """Run a scraper and return jobs"""

    try:
        print("DEBUG: asyncio imported\n")
        from datetime import datetime
        
        # Write debug info to a log file
        with open("/tmp/orchestrator_debug.log", "a") as log_file:
            log_file.write(f"\n=== Starting scraper {name} ===\n")
            attrs = [attr for attr in dir(module) if not attr.startswith('_') and attr != 'Job']
            log_file.write(f"Module attributes: {attrs}\n")
        
        # Find the main scraper class in the module
        scraper_class = None
        
        # Check for common class names
        for class_name in ['Scraper', 'Crawler', 'Spider', 'Extractor']:
            if hasattr(module, class_name):
                attr = getattr(module, class_name)
                if isinstance(attr, type):
                    # Check that this class is defined in the current module, not imported
                    if getattr(attr, '__module__', None) == module.__name__:
                        scraper_class = attr
                        with open("/tmp/orchestrator_debug.log", "a") as log_file:
                            log_file.write(f"Found {class_name} class: {attr}\n")
                        break
        
        # If not found, look for any class defined in the module (excluding exceptions)
        if scraper_class is None:
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                # Check if it's a class and defined in this module (not imported)
                if isinstance(attr, type) and attr_name != "Job" and not attr_name.startswith('_'):
                    # Get the module where the class was defined
                    class_module = getattr(attr, '__module__', None)
                    if class_module == module.__name__:
                        scraper_class = attr
                        with open("/tmp/orchestrator_debug.log", "a") as log_file:
                            log_file.write(f"Found class {attr_name}: {attr}\n")
                        break
        
        with open("/tmp/orchestrator_debug.log", "a") as log_file:
            log_file.write(f"scraper_class = {scraper_class}\n")
        
        if scraper_class is None:
            # Fallback: look for a run function directly
            if hasattr(module, "run"):
                result = module.run()
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"module.run() returned: {result}\n")
                if hasattr(result, "__await__"):
                    return asyncio.run(result)
                return result
            elif hasattr(module, "scrape_jobs"):
                result = module.scrape_jobs()
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"module.scrape_jobs() returned: {result}\n")
                if hasattr(result, "__await__"):
                    return asyncio.run(result)
                return result
            elif hasattr(module, "scrape"):
                result = module.scrape()
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"module.scrape() returned: {result}\n")
                if hasattr(result, "__await__"):
                    return asyncio.run(result)
                return result
            else:
                raise ValueError(f"No suitable scraper class or function found in {name} module")
        
        # Instantiate the scraper class
        with open("/tmp/orchestrator_debug.log", "a") as log_file:
            log_file.write(f"Instantiating {scraper_class} from {module.__name__}\n")
        try:
            scraper = scraper_class()
        except Exception as e:
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"Error instantiating {scraper_class}: {e}\n")
            import traceback
            traceback.print_exc()
            raise
        
        with open("/tmp/orchestrator_debug.log", "a") as log_file:
            log_file.write(f"scraper instance: {scraper}\n")
            log_file.write(f"scraper methods: {dir(scraper)}\n")
        
        if hasattr(scraper, "run"):
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"Calling scraper.run()...\n")
            result = scraper.run()
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"scraper.run() returned: {result}\n")
            if hasattr(result, "__await__"):
                result = asyncio.run(result)
            else:
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"scraper.run() did not return a coroutine, returning as-is: {result}\n")
        elif hasattr(scraper, "scrape_jobs"):
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"Calling scraper.scrape_jobs()...\n")
            result = scraper.scrape_jobs()
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"scraper.scrape_jobs() returned: {result}\n")
            if hasattr(result, "__await__"):
                result = asyncio.run(result)
            else:
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"scraper.scrape_jobs() did not return a coroutine, returning as-is: {result}\n")
        elif hasattr(scraper, "scrape"):
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"Calling scraper.scrape()...\n")
            result = scraper.scrape()
            with open("/tmp/orchestrator_debug.log", "a") as log_file:
                log_file.write(f"scraper.scrape() returned: {result}\n")
            if hasattr(result, "__await__"):
                result = asyncio.run(result)
            else:
                with open("/tmp/orchestrator_debug.log", "a") as log_file:
                    log_file.write(f"scraper.scrape() did not return a coroutine, returning as-is: {result}\n")
        else:
            raise ValueError(f"Scraper class {scraper_class.__name__} has no run/scrape_jobs/scrape method")
        return result
    except Exception as e:
        with open("/tmp/orchestrator_debug.log", "a") as log_file:
            log_file.write(f"[Orchestrator] Error running {name}: {e}\n")
        import traceback
        traceback.print_exc()
    return []


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
            jobs = run_scraper(module, source_name)
            if jobs:
                print(f"[Orchestrator] {source_name}: {len(jobs)} jobs")
                all_jobs.extend(jobs)
                seen_sources.add(source_name)
    
    print(f"\n[Orchestrator] Total sources loaded: {len(seen_sources)}")
    return all_jobs

def deduplicate_jobs(jobs):
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

def save_jobs(jobs, path):
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