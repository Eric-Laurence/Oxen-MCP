# MCP Simple Chatbot

This example demonstrates how to integrate the Model Context Protocol (MCP) into a simple CLI chatbot. The implementation showcases MCP's flexibility by supporting multiple tools through MCP servers and is compatible with any LLM provider that follows OpenAI API standards.

## Requirements

- Python 3.10
- `python-dotenv`
- `requests`
- `mcp`
- `uvicorn`

## Installation

1. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   Create a `.env` file in the root directory and add your API key:

   ```plaintext
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Configure servers:**

   The `servers_config.json` follows the same structure as Claude Desktop, allowing for easy integration of multiple servers. 
   Here's the current configuration for Oxen integration:

   ```json
   {
     "mcpServers": {
       "oxen-search": {
         "command": "uv",
         "args": ["run", "mcp-oxen-search", "--repo", "elau/Oxen-MCP-Example", "--dataframe", "question_answer_pairs.jsonl"],
         "env": {
           "OPENAI_API_KEY": "${OPENAI_API_KEY}"
         }
       }
     }
   }
   ```
   Environment variables are supported as well. Note how the OpenAI API key is referenced using `${OPENAI_API_KEY}` to use the value from your .env file.

   You can also configure multiple servers at once:
   ```json
   {
     "mcpServers": {
       "oxen-search": {
         "command": "uv",
         "args": ["run", "mcp-oxen-search", "--repo", "elau/Oxen-MCP-Example", "--dataframe", "question_answer_pairs.jsonl"],
         "env": {
           "OPENAI_API_KEY": "${OPENAI_API_KEY}"
         }
       },
       "other-server": {
         "command": "command-name",
         "args": ["server-name", "--additional-args"],
         "env": {
           "API_KEY": "${API_KEY}"
         }
       }
     }
   }
   ```

## Usage

1. **Make sure your server is properly configured:**

   The `servers_config.json` file is already configured with the correct repository and dataframe:
   ```json
   "args": ["run", "mcp-oxen-search", "--repo", "elau/Oxen-MCP-Example", "--dataframe", "question_answer_pairs.jsonl"]
   ```

2. **Run the client:**

   ```bash
   cd mcp_simple_chatbot
   python main.py
   ```

   The client will automatically start the configured MCP servers and connect to them.

3. **Interact with the assistant:**
   
   The assistant will automatically detect available tools and can respond to queries based on the tools provided by the configured servers.

4. **Exit the session:**

   Type `quit` or `exit` to end the session.

## Architecture

- **Tool Discovery**: Tools are automatically discovered from configured servers.
- **System Prompt**: Tools are dynamically included in the system prompt, allowing the LLM to understand available capabilities.
- **Server Integration**: Supports any MCP-compatible server, tested with various server implementations including Uvicorn and Node.js.

### Class Structure
- **Configuration**: Manages environment variables and server configurations
- **Server**: Handles MCP server initialization, tool discovery, and execution
- **Tool**: Represents individual tools with their properties and formatting
- **LLMClient**: Manages communication with the LLM provider
- **ChatSession**: Orchestrates the interaction between user, LLM, and tools

### Logic Flow

1. **Tool Integration**:
   - Tools are dynamically discovered from MCP servers
   - Tool descriptions are automatically included in system prompt
   - Tool execution is handled through standardized MCP protocol

2. **Runtime Flow**:
   - User input is received
   - Input is sent to LLM with context of available tools
   - LLM response is parsed:
     - If it's a tool call → execute tool and return result
     - If it's a direct response → return to user
   - Tool results are sent back to LLM for interpretation
   - Final response is presented to user


