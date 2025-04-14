import sys
import asyncio
import json
from loguru import logger
from app.services.llm import LLMService, ReportGenerationRequest, ReportGenerationResponse

async def main():
    try:
        print("Testing report generation with Gmail data...")
        service = LLMService()
        
        # Create a simple report generation request
        request = ReportGenerationRequest(
            title="Test Knowledge Summary",
            report_type="knowledge_summary",
            time_period="last_7_days",
            data_sources=["gmail"],
            query_filter="",
            sections=["key_findings", "action_items"]
        )
        
        print(f"Request: {request}")
        
        # Generate the report
        print("\nGenerating report (this may take a while)...")
        response = await service.generate_report(request)
        
        print(f"\nReport status: {response.status}")
        print(f"Data sources: {response.data_sources}")
        print(f"Token usage: {response.token_usage}")
        print(f"Confidence score: {response.confidence_score}")
        
        # Print the report content in a readable format
        print("\nReport content:")
        for section, content in response.content.items():
            print(f"\n--- {section.upper()} ---")
            print(content)
        
        # Print the summary
        print("\nSummary:")
        print(response.summary)
        
        # Save the report to a file for easier examination
        with open('test_report_output.json', 'w') as f:
            # Convert the Pydantic model to a dictionary and then to JSON
            json.dump(response.dict(), f, indent=2, default=str)
        print("\nFull report saved to test_report_output.json")
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 