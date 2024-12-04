from scheme_matcher import SchemeMatcher
import json
import asyncio
from rich.console import Console
from rich.table import Table

async def test_scheme_matcher():
    # Initialize matcher and console
    matcher = SchemeMatcher()
    console = Console()
    
    # Sample user data
    user_data = {
        "age": 35,
        "gender": "Male",
        "occupation": "Farmer",
        "annual_income": 300000,
        "state": "Karnataka",
        "category": "General",
        "specific_needs": ["Agriculture Support"]
    }
    
    console.print("\n[bold blue]Testing Enhanced Scheme Matcher...[/bold blue]")
    console.print("\n[bold green]User Profile:[/bold green]")
    console.print(json.dumps(user_data, indent=2))
    
    # Get matches from vector database
    console.print("\n[bold yellow]Searching for matching schemes...[/bold yellow]")
    matches = await matcher.find_matches(user_data, top_k=5)
    
    # Create results table
    table = Table(title="Matching Schemes")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Priority", style="magenta")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Recommendation", style="yellow")
    
    # Add matches to table
    for match in matches:
        table.add_row(
            match.name,
            match.priority_level,
            f"{match.relevance_score:.2f}",
            match.recommendation
        )
    
    # Display results table
    console.print(table)
    
    # Show detailed analysis for top match
    if matches:
        top_match = matches[0]
        console.print(f"\n[bold green]Detailed Analysis of Top Match:[/bold green]")
        console.print(f"\n[bold cyan]Scheme:[/bold cyan] {top_match.name}")
        console.print(f"[bold cyan]Description:[/bold cyan] {top_match.description}")
        
        console.print("\n[bold cyan]Benefits:[/bold cyan]")
        for benefit in top_match.benefits:
            console.print(f"• {benefit}")
        
        console.print("\n[bold cyan]Eligibility Status:[/bold cyan]")
        for criterion, status in top_match.eligibility_status.items():
            icon = "✓" if status else "✗"
            color = "green" if status else "red"
            console.print(f"[{color}]{icon} {criterion.title()}[/{color}]")
        
        console.print(f"\n[bold cyan]Recommendation:[/bold cyan] {top_match.recommendation}")

def main():
    asyncio.run(test_scheme_matcher())

if __name__ == "__main__":
    main() 