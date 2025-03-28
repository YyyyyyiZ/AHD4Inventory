import json
import os
from typing import Optional


def extract(folder_name: Optional[str] = None) -> None:
    """Extract code from pop_best folders and save to code_extracted.txt

    Args:
        folder_name: Optional specific folder to process. If None, processes all pop_best folders.
    """
    output_file = "evaluation/code_extracted.txt"

    if folder_name:
        # Process specific folder
        folders_to_process = [os.path.join(folder_name, "pops_best")]
    else:
        # Find all pops_best folders in the directory tree
        folders_to_process = []
        for root, dirs, files in os.walk("."):
            if "pops_best" in dirs:
                folders_to_process.append(os.path.join(root, "pops_best"))

    with open(output_file, "w") as outfile:
        for pops_best_folder in folders_to_process:
            if not os.path.exists(pops_best_folder):
                continue

            print(f"Processing folder: {pops_best_folder}")

            # Process all JSON files in the pops_best folder
            for filename in os.listdir(pops_best_folder):
                if not filename.endswith(".json"):
                    continue

                filepath = os.path.join(pops_best_folder, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        for index, item in enumerate(data):
                            process_item(item, outfile, pops_best_folder, filename, index)
                    else:
                        process_item(data, outfile, pops_best_folder, filename)

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error processing {filepath}: {e}")

    print(f"Extracted code saved to {output_file}")


def process_item(item: dict, outfile, folder_path: str, filename: str, index: Optional[int] = None) -> None:
    """Helper function to process a single JSON item and write code to file"""
    if "code" not in item:
        return

    # Extract the code string
    code_str = item["code"]

    # Remove surrounding quotes if present
    if code_str.startswith('"') and code_str.endswith('"'):
        code_str = code_str[1:-1]

    # Replace \n with actual newlines
    code_str = code_str.replace("\\n", "\n")

    # Write source information
    source_info = f"# Source: {os.path.normpath(folder_path)}/{filename}"
    if index is not None:
        source_info += f" (item {index})"

    # Write objective if available
    objective = item.get("objective", "unknown")

    # Write to file with separator
    outfile.write(f"{source_info}\n")
    outfile.write(f"# Objective: {objective}\n")
    outfile.write(code_str)
    outfile.write("\n\n" + "=" * 80 + "\n\n")


if __name__ == "__main__":
    # Example usage:
    # extract()  # Processes all pops_best folders
    # extract("results_None_None_low")  # Processes specific folder
    extract()