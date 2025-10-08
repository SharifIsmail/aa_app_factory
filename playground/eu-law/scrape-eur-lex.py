import argparse
from datetime import datetime, timedelta
from pathlib import Path
from rdflib import Graph
from rdflib.query import ResultRow
import pandas as pd

def scrape_eur_lex(start_date: datetime, end_date: datetime, output_dir: Path):
    """Scrape EUR-Lex data for a given date range and save results to Excel."""
    # Create a list to store all results
    all_results = []
    
    current_date = start_date
    while current_date <= end_date:
        print(f"Processing date: {current_date.date()}")
        g = Graph()
        g.parse("https://publications.europa.eu/webapi/rdf/sparql")

        # Retrieves data, expression url, title, and PDF url for each legal act published on the selected date in OJ
        legal_act_query = f"""
        PREFIX cdm:<http://publications.europa.eu/ontology/cdm#>
        PREFIX eli:<http://data.europa.eu/eli/ontology#>
        PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
        PREFIX dc:<http://purl.org/dc/elements/1.1/>
        PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl:<http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?date ?act ?expression_title ?item
        where {{
            SERVICE <https://publications.europa.eu/webapi/rdf/sparql> {{
                ?work owl:sameAs ?act.
                ?work cdm:official-journal-act_date_publication "{current_date.date()}"^^<http://www.w3.org/2001/XMLSchema#date>
                FILTER (regex(?act,'/oj/')).
                ?work cdm:official-journal-act_date_publication ?date.

                ?expression cdm:expression_belongs_to_work ?work.
                ?expression cdm:expression_title ?expression_title.
                ?expression cdm:expression_uses_language ?languageConcept.
    		    ?languageConcept dc:identifier "DEU".

                ?manifestation cdm:manifestation_manifests_expression ?expression;
                               cdm:manifestation_type ?manifestation_type.
                FILTER(?manifestation_type = "pdfa2a"^^<http://www.w3.org/2001/XMLSchema#string>).
                
                ?item cdm:item_belongs_to_manifestation ?manifestation.
            }}
        }} LIMIT 1000
        """
        result = g.query(legal_act_query)
        for row in result:
            # Convert row to dictionary and append to results
            # Access values using the variable names from the SPARQL query
            row_dict = {
                'date': row[0],
                'expression_url': row[1],
                'title': row[2],
                'pdf_url': row[3]
            }
            all_results.append(row_dict)
            
        current_date += timedelta(days=1)
    
    # Convert results to DataFrame
    df = pd.DataFrame(all_results)
    
    # Create Excel filename with date range
    excel_filename = output_dir / f"eur_lex_data_{start_date.date()}_to_{end_date.date()}.xlsx"
    
    # Write to Excel
    df.to_excel(excel_filename, index=False)
    print(f"\nResults have been saved to: {excel_filename}")
    print(f"Total records found: {len(df)}")


def validate_date(date_str: str) -> datetime:
    """Validate that a string is a valid ISO format date (YYYY-MM-DD)."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{date_str}' is not a valid date in YYYY-MM-DD format")


def validate_directory(path: str | Path) -> Path:
    """Validate and create directory if it doesn't exist."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def main():
    parser = argparse.ArgumentParser(
        description="Scrape EUR-Lex data for a given date range",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "start_date",
        type=validate_date,
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "end_date",
        type=validate_date,
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "output_dir",
        type=validate_directory,
        help="Directory to store scraped data"
    )

    args = parser.parse_args()

    # Validate that end_date is not before start_date
    if args.end_date < args.start_date:
        parser.error("End date must be after start date")

    print(f"Scraping EUR-Lex data from {args.start_date.date()} to {args.end_date.date()}")
    print(f"Data will be stored in: {args.output_dir}")

    scrape_eur_lex(args.start_date, args.end_date, args.output_dir)


if __name__ == "__main__":
    main()
