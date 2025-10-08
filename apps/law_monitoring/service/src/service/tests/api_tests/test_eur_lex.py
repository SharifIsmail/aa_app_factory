#!/usr/bin/env python3
"""
Test script for the updated EUR-Lex service
"""

import sys
from datetime import datetime
from pathlib import Path

# Add the service directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from service.law_core.eur_lex_service import EurLexService


def test_eur_lex_service() -> bool:
    """Test the EUR-Lex service with the new range-based query"""

    print("Testing EUR-Lex Service...")

    # Initialize the service
    service = EurLexService()

    # Test with a more recent date range
    start_date = datetime(2024, 6, 1)  # June 1, 2024
    end_date = datetime(2024, 6, 30)  # June 30, 2024

    print(f"Querying for legal acts from {start_date.date()} to {end_date.date()}")

    # Debug: Show the SPARQL query that will be generated for the start date
    query = service._build_sparql_query(start_date, 10)
    print(f"\nGenerated SPARQL Query (for {start_date.date()}):")
    print("=" * 50)
    print(query)
    print("=" * 50)

    try:
        response = service.get_legal_acts_by_date_range(start_date, end_date, limit=10)

        print(f"\nFound {response.total_count} legal acts")

        if response.total_count == 0:
            print("No legal acts found for this date range.")
            print("This could mean:")
            print("1. No acts were published in this period")
            print("2. The EUR-Lex endpoint might be having issues")
            print("3. The query syntax might need adjustment")

            # Try with an even broader range
            print("\nTrying broader range...")
            broad_start = datetime(2024, 1, 1)
            broad_end = datetime(2024, 12, 31)
            print(
                f"Querying for legal acts from {broad_start.date()} to {broad_end.date()}"
            )

            broad_response = service.get_legal_acts_by_date_range(
                broad_start, broad_end, limit=5
            )
            print(f"Found {broad_response.total_count} legal acts in broader range")

            if broad_response.total_count > 0:
                print("Success with broader range! Showing first few:")
                for i, act in enumerate(broad_response.legal_acts[:3], 1):
                    print(f"\n{i}. {act.title}")
                    print(f"   Publication Date: {act.publication_date}")

        else:
            for i, act in enumerate(response.legal_acts[:5], 1):  # Show first 5
                print(f"\n{i}. {act.title}")
                print(f"   Publication Date: {act.publication_date}")
                print(f"   URL: {act.expression_url}")
                print(f"   PDF: {act.pdf_url}")
                if act.eurovoc_labels:
                    print(f"   Topics: {act.eurovoc_labels}")
                # Show additional date metadata
                if act.document_date:
                    print(f"   Document Date: {act.document_date}")
                if act.effect_date:
                    print(f"   Effect Date: {act.effect_date}")
                if act.end_validity_date:
                    print(f"   End Validity: {act.end_validity_date}")
                if act.notification_date:
                    print(f"   Notification Date: {act.notification_date}")

            if response.total_count > 5:
                print(f"\n... and {response.total_count - 5} more acts")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_eur_lex_service()
    if success:
        print("\n✅ Test completed!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
