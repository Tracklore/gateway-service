#!/bin/bash

# A script to create or update GitHub issues from a Markdown file.
# It reads the file line-by-line, handling multi-line descriptions and code blocks.

ISSUES_FILE="github_issues.md"

if [ ! -f "$ISSUES_FILE" ]; then
    echo "Error: The file '$ISSUES_FILE' was not found."
    exit 1
fi

# Function to process a single issue's data
process_issue() {
    # Trim leading/trailing whitespace from the variables
    current_title=$(echo "$current_title" | xargs)
    # The body needs careful trimming to preserve internal newlines
    current_body=$(echo -e "$current_body" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    current_labels=$(echo "$current_labels" | xargs)

    # Exit if the title is empty
    if [[ -z "$current_title" ]]; then
        return
    fi

    echo "Processing issue: $current_title"

    # Search for an existing issue with the exact title (open or closed)
    issue_data=$(gh issue list --search "in:title \"$current_title\"" --limit 1 --json number,state -q ".[0]")

    if [[ -n "$issue_data" && "$issue_data" != "null" ]]; then
        issue_number=$(echo "$issue_data" | jq -r ".number")
        issue_state=$(echo "$issue_data" | jq -r ".state")

        echo "Found existing issue #$issue_number (State: $issue_state). Updating..."
        gh issue edit "$issue_number" --title "$current_title" --body "$current_body"
        
        # Update labels if they are provided
        if [[ ! -z "$current_labels" ]]; then
            old_labels=$(gh issue view "$issue_number" --json labels -q '.labels.[].name' | tr '\n' ',' | sed 's/,$//')
            if [[ -n "$old_labels" ]]; then
                gh issue edit "$issue_number" --remove-label "$old_labels"
            fi
            gh issue edit "$issue_number" --add-label "$current_labels"
        fi
        
        # Reopen the issue if it was closed
        if [[ "$issue_state" == "CLOSED" ]]; then
            echo "Re-opening issue #$issue_number."
            gh issue reopen "$issue_number"
        fi
    else
        echo "No existing issue found for '$current_title'. Creating a new one..."
        gh issue create --title "$current_title" --body "$current_body" --label "$current_labels"
    fi
    echo "-------------------------------------"
}

# --- PARSING LOGIC ---
current_title=""
current_body=""
current_labels=""

# Read the file line by line
while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "---" ]]; then
        process_issue
        current_title=""
        current_body=""
        current_labels=""
    elif [[ "$line" =~ ^##[[:space:]]+[0-9]*\.?[[:space:]]*(.*) ]]; then
        current_title="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^\*\*Labels:\*\*[[:space:]]*(.*) ]]; then
        current_labels="${BASH_REMATCH[1]}"
    else
        current_body+="$line\n"
    fi
done < "$ISSUES_FILE" # <-- THE FIX IS HERE: Redirect the file into the loop

# After the loop finishes, process the very last issue in the file
process_issue

echo "Script finished. All issues have been processed."