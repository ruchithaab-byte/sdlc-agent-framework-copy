# Linear Integration Setup Instructions

## Overview
To create Linear epics and issues, you need to configure your Linear API credentials.

## Setup Steps

### 1. Get Your Linear API Key

1. Go to [Linear Settings > API](https://linear.app/settings/api)
2. Click "Create new key"
3. Give it a descriptive name (e.g., "SDLC Agent Framework")
4. Copy the generated API key (starts with `lin_api_`)

### 2. Get Your Linear Team ID

1. Go to your Linear workspace
2. Navigate to your team's page
3. The Team ID is in the URL: `https://linear.app/[workspace]/team/[TEAM_ID]/...`
4. Alternatively, you can use the Linear API to list teams:
   ```bash
   curl -X POST https://api.linear.app/graphql \
     -H "Authorization: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query":"{ teams { nodes { id name } } }"}'
   ```

### 3. Configure Environment Variables

Edit your `.env` file and uncomment/update the Linear configuration:

```bash
# Linear Integration
LINEAR_API_KEY=lin_api_your-actual-key-here
LINEAR_TEAM_ID=your-actual-team-id-here
```

### 4. Verify Setup

Run the test script to verify your configuration:

```bash
python3 .claude/skills/linear-integration/create_greeting_epic.py
```

If successful, you'll see output with your Epic ID, Identifier, and URL.

## Example Epic Details

**Title:** Simple Greeting Application - Say Hello and Stop

**Description:** A minimal application that demonstrates basic lifecycle management with greeting functionality. The application should:
- Display a greeting message to users upon start
- Provide a clear and simple way to stop/exit the application
- Follow best practices for user experience in CLI applications

**Key Features:**
1. Immediate greeting on startup
2. Clear exit mechanism (via 'stop' command)
3. Graceful signal handling (Ctrl+C)
4. Proper exit codes
5. Minimal dependencies and fast startup

This epic will track the development of this simple yet well-designed greeting application.

## Troubleshooting

- **Error: LINEAR_API_KEY and LINEAR_TEAM_ID must be set**: Make sure you've uncommented the lines in `.env` and added your actual credentials
- **Error: Linear API error**: Check that your API key is valid and has the correct permissions
- **Error: Team not found**: Verify your Team ID is correct

## Security Note

Never commit your `.env` file with actual credentials to version control. The `.gitignore` file should already exclude it.
