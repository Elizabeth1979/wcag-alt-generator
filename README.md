# WCAG-Compliant Alt Text Generator

A Python tool that automatically analyzes web pages and generates WCAG-compliant alt text for images using the Claude AI model. The tool extracts images, understands their context, and generates appropriate alt text following Web Content Accessibility Guidelines (WCAG) 2.1.

## Features

- **Web Page Analysis**: Extracts images and their surrounding context from any web page
- **Context-Aware**: Captures surrounding text, captions, and structural context
- **WCAG Compliance**:
  - Identifies image roles (decorative, functional, informative)
  - Generates appropriate alt text based on image role and context
  - Follows WCAG 2.1 guidelines for alt text creation
- **Structured Output**: Generates JSON reports containing:
  - Image source URLs
  - Current and suggested alt text
  - Contextual information
  - Role classification

## Prerequisites

- Python 3.x
- Anthropic API key

## Installation

1. Clone the repository

```bash
git clone [your-repo-url]
cd wcag-alt-generator
```

2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Anthropic API key:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

```python
from src.alt_text_generator import WCAGAltTextGenerator

# Initialize the generator
generator = WCAGAltTextGenerator()

# Process a webpage
results = generator.process_url("https://example.com")

# Results are automatically saved to a JSON file in the output directory
```

### Example Output

The tool generates a JSON file with the following structure:

```json
{
  "url": "https://example.com",
  "analysis_timestamp": "2024-03-20T14:30:22.123456",
  "total_images": 5,
  "images": [
    {
      "src": "example.jpg",
      "existing_alt": "Current alt text",
      "role": "informative",
      "context": {
        "before": "Text before the image",
        "after": "Text after the image"
      },
      "suggested_alt": "Generated alt text"
    }
  ]
}
```

## WCAG Compliance Details

The tool follows these WCAG 2.1 guidelines:

1. **Role-Based Alt Text**:
   - Decorative images: Empty alt text
   - Functional images (in links/buttons): Describes the action
   - Informative images: Concise, meaningful descriptions

2. **Context Awareness**:
   - Avoids redundancy with surrounding text
   - Considers image captions and titles
   - Adapts to the image's role in the page

3. **Best Practices**:
   - Avoids phrases like "image of" or "picture of"
   - Keeps descriptions concise but informative
   - Prioritizes meaningful content over visual details

## Project Structure

``` text
wcag-alt-generator/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   └── alt_text_generator.py
├── tests/
├── docs/
└── output/
```

## Dependencies

- requests: For fetching web pages
- beautifulsoup4: For HTML parsing
- anthropic: For accessing Claude AI
- python-dotenv: For environment variable management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- Follows [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html)