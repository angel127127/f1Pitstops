import argparse
from qualiGraphs import getQualiData

def main():
    parser = argparse.ArgumentParser(
        description="Generate F1 Qualifying Graphs using FastF1 data")
    parser.add_argument("location", type=str, help="Grand Prix location")
    parser.add_argument("year", type=int, help="Year of race")
    args=parser.parse_args()
    print(f"Fetching qualifying data for {args.location} {args.year}...")
    getQualiData(args.location, args.year, False)

if __name__ == "__main__":
    main()
