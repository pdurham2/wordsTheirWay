import pandas as pd
from scorer import get_feature_guide, score_all, write_output

LEVEL_PROMPT = """Enter the feature guide you want to use.
Valid options are:
    1) primary
    2) elementary
    3) upper-level
Choice: """


def prompt_level():
    while True:
        result = get_feature_guide(input(LEVEL_PROMPT))
        if result is not None:
            return result


def prompt_test_file():
    while True:
        path = input("Enter the name of the file to score, or q to quit: ").strip()
        if path == "q":
            return None, None
        try:
            test = pd.read_excel(path)
            test = test.rename(columns={"name": "feature"}).set_index("feature")
            return path, test
        except FileNotFoundError:
            print("File not found, please try again.")


def main():
    while True:
        level, feature_guide = prompt_level()

        path, test = prompt_test_file()
        if path is None:
            break

        results = score_all(level, feature_guide, test)
        if results is None:
            print("Scoring failed due to missing data. Exiting.")
            break

        out_path = path.rsplit(".", 1)[0] + "_output.xlsx"
        write_output(out_path, results)
        print(f"Output saved to: {out_path}")

        again = ""
        while again not in ("y", "n"):
            again = input("Would you like to score another workbook? (y/n): ").strip()
        if again == "n":
            break


if __name__ == "__main__":
    main()
