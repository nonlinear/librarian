# Project Inquiry

## Instructions for AI

1. **Understand the User's Question**:

   - Parse the user's input to identify key elements such as project names, issue types, statuses, dates, and other relevant filters.

2. **Translate to JQL (Jira Query Language)**:

   - Use the following structure to build the JQL query:
     ```
     assignee = currentUser() AND issuetype IS NOT EMPTY AND status IN ("Open", "In Progress")
     ```
   - Avoid hardcoding specific issue types like `Project`. Instead, use `issuetype IS NOT EMPTY` to ensure compatibility.
   - Always validate the query structure to avoid syntax errors.

3. **Generate the Advanced Search URL**:

   - Base URL: `https://wiley-global.atlassian.net/issues/?jql=`
   - Encode the JQL query and append it to the base URL.

4. **Provide the Result**:
   - Return only a concise list of interpretations and their corresponding URLs, formatted as follows:
     ```
     - [Interpretation 1](<Advanced Search URL>)
     - [Interpretation 2](<Advanced Search URL>)
     - [Interpretation 3](<Advanced Search URL>)
     ```

## Example Workflow

1. **User Input**: "What do I need to do next week?"
2. **Generated JQL**: `assignee = currentUser() AND issuetype IS NOT EMPTY AND status IN ("Open", "In Progress") AND due >= startOfWeek() AND due <= endOfWeek()`
3. **Generated URL**: `https://wiley-global.atlassian.net/issues/?jql=assignee%20%3D%20currentUser()%20AND%20issuetype%20IS%20NOT%20EMPTY%20AND%20status%20IN%20(%22Open%22,%20%22In%20Progress%22)%20AND%20due%20%3E%3D%20startOfWeek()%20AND%20due%20%3C%3D%20endOfWeek()`

## References

- [JQL Operators](https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-jql-operators/)
- [JQL Functions](https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-jql-functions/)
- [JQL Keywords](https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-keywords/)
