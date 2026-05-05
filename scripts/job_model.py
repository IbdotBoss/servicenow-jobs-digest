"""
Enhanced Job Data Model for ServiceNow Jobs Digest
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import re

@dataclass
class Job:
    """Enhanced job data model with metadata and tags"""
    
    # Core fields
    title: str
    company: str
    location: str
    date: str  # YYYY-MM-DD format
    link: str
    
    # Source tracking
    source: str  # e.g., 'hunt_uk', 'linkedin', 'indeed'
    
    # Sponsorship & clearance
    sponsorship_confirmed: bool = False  # Could be "required", "provided", etc.
    security_clearance: bool = False
    remote_work: Optional[str] = None  # Could be "hybrid", "remote", "onsite"
    
    # Metadata & tags
    tags: List[str] = None
    job_type: str = "permanent"  # permanent, contract, temp, internship
    experience_level: str = "mid"  # entry, mid, senior, executive
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "GBP"
    remote: bool = False
    posted_date: Optional[datetime] = None
    
    # Internal tracking
    scraped_at: datetime = None
    hash: str = None
    
    def __post_init__(self):
        """Initialize optional fields and generate hash"""
        if self.tags is None:
            self.tags = []
        
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
        
        # Generate unique hash based on key fields
        self.generate_hash()
    
    def generate_hash(self):
        """Generate unique hash for deduplication"""
        key = f"{self.company}_{self.title}_{self.location}".lower()
        # Remove non-alphanumeric and normalize
        key = re.sub(r'[^a-z0-9]', '', key)
        self.hash = hash(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        data = asdict(self)
        # Convert datetime objects to strings
        if self.scraped_at:
            data['scraped_at'] = self.scraped_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job instance from dictionary"""
        # Convert string dates back to datetime
        if 'scraped_at' in data and isinstance(data['scraped_at'], str):
            data['scraped_at'] = datetime.fromisoformat(data['scraped_at'])
        
        return cls(**data)
    
    def to_markdown_row(self) -> str:
        """Format as markdown table row"""
        sponsorship = '✓' if self.sponsorship_confirmed else '✗'
        sc = '✓' if self.security_clearance else '✗'
        salary = f"£{self.salary_min:,} - £{self.salary_max:,}" if self.salary_min else '-'
        
        return f"| {self.date} | [{self.title}]({self.link}) | {self.company} | {self.location} | {salary} | {sponsorship} | {sc} | [View]({self.link}) |"
    
    def to_html_row(self) -> str:
        """Format as HTML table row"""
        sponsorship_class = "sponsorship-yes" if self.sponsorship_confirmed else "sponsorship-no"
        sc_class = "sc-yes" if self.security_clearance else "sc-no"
        
        salary = f"£{self.salary_min:,} - £{self.salary_max:,}" if self.salary_min else '-'
        
        return f"""
        <tr class="{sponsorship_class} {sc_class}">
            <td class="date">{self.date}</td>
            <td class="title"><a href="{self.link}" target="_blank">{self.title}</a></td>
            <td class="company">{self.company}</td>
            <td class="location">{self.location}</td>
            <td class="salary">{salary}</td>
            <td class="sponsorship">{sponsorship_class.split('-')[1].title()}</td>
            <td class="sc">{sc_class.split('-')[1].title()}</td>
            <td class="actions"><a href="{self.link}" class="btn-view">View</a></td>
        </tr>
        """

# Helper functions
def parse_date(date_str: str) -> str:
    """Parse various date formats to YYYY-MM-DD"""
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%d %B %Y"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If parsing fails, return today's date
    return datetime.now().strftime("%Y-%m-%d")

def normalize_location(location: str) -> str:
    """Normalize location names"""
    location = location.lower()
    
    # Common patterns
    if "uk" in location or "united kingdom" in location:
        return "UK"
    if "london" in location:
        return "London, UK"
    if "manchester" in location:
        return "Manchester, UK"
    if "birmingham" in location:
        return "Birmingham, UK"
    
    return location.title()

def extract_tags(title: str, description: str) -> List[str]:
    """Extract tags from job title and description"""
    tags = []
    
    # Job type patterns
    if any(word in title.lower() for word in ['contract', 'contract', 'temp', 'internship']):
        tags.append('contract')
    else:
        tags.append('permanent')
    
    # Experience level
    if any(word in title.lower() for word in ['junior', 'entry', 'graduate']):
        tags.append('entry')
    elif any(word in title.lower() for word in ['senior', 'lead', 'principal', 'architect']):
        tags.append('senior')
    else:
        tags.append('mid')
    
    # Remote work
    if 'remote' in title.lower() or 'hybrid' in title.lower():
        tags.append('remote')
    
    return tags

# Serialization functions
def jobs_to_json(jobs: List[Job], path: str):
    """Save jobs to JSON file"""
    import json
    data = [job.to_dict() for job in jobs]
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def jobs_from_json(path: str) -> List[Job]:
    """Load jobs from JSON file"""
    import json
    with open(path, 'r') as f:
        data = json.load(f)
    return [Job.from_dict(item) for item in data]

if __name__ == "__main__":
    # Test the model
    job = Job(
        title="ServiceNow Developer",
        company="ABC Company",
        location="London, UK",
        date="2026-01-15",
        link="https://example.com/job/123",
        source="linkedin",
        sponsorship_confirmed=True,
        security_clearance=False,
        tags=["permanent", "mid", "remote"],
        job_type="permanent",
        experience_level="mid",
        salary_min=50000,
        salary_max=60000
    )
    
    print("Job hash:", job.hash)
    print("Markdown row:", job.to_markdown_row())
    print("HTML row:", job.to_html_row())