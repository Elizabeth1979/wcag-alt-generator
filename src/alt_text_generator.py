import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

class WCAGAltTextGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def fetch_page_content(self, url: str) -> str:
        """Fetch webpage content with proper headers."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; WCAGAltTextBot/1.0)'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Error fetching URL: {str(e)}")

    def _get_surrounding_text(self, img_tag, context_range: int = 100) -> Dict[str, str]:
        """
        Get meaningful text content around the image within a specified character range.
        Excludes script, style, code, and non-content text.
        """
        def is_valid_text(element):
            if not element or not isinstance(element, str):
                return False
            
            # Check if element is within unwanted tags
            parent = element.parent if hasattr(element, 'parent') else None
            if parent and parent.name in ['script', 'style', 'code', 'noscript']:
                return False
            
            # Check if text is actual content (not CSS/JS)
            text = element.strip()
            if not text:
                return False
            
            # Filter out common code patterns
            code_patterns = [
                '{',
                '}',
                '//',
                '/*',
                '*/',
                '<script',
                '<style',
                '@media',
                'function(',
                'var ',
                'let ',
                'const ',
                '.css',
                '.js',
                'window.',
                'document.'
            ]
            
            if any(pattern in text for pattern in code_patterns):
                return False
            
            return True

        previous_text = []
        next_text = []
        
        # Get previous text
        current = img_tag.find_previous(string=True)
        while current and len(' '.join(previous_text)) < context_range:
            if is_valid_text(current):
                previous_text.insert(0, current.strip())
            current = current.find_previous(string=True)

        # Get next text
        current = img_tag.find_next(string=True)
        while current and len(' '.join(next_text)) < context_range:
            if is_valid_text(current):
                next_text.append(current.strip())
            current = current.find_next(string=True)

        return {
            'before': ' '.join(previous_text),
            'after': ' '.join(next_text)
        }

    def _determine_image_role(self, img_tag) -> Dict:
        """
        Determine the role and characteristics of the image based on WCAG guidelines.
        Also extracts caption text if present.
        """
        role_info = {
            'is_decorative': False,
            'is_functional': False,
            'is_informative': False,
            'has_caption': False,
            'in_content': False,
            'in_header': False,
            'in_navigation': False,
            'caption_text': ''
        }
        
        # Check if decorative
        if (img_tag.get('role') == 'presentation' or 
            img_tag.get('aria-hidden') == 'true' or
            (not img_tag.get('alt') and not img_tag.find_parent('a'))):
            role_info['is_decorative'] = True
            return role_info

        # Check if functional (part of a link or button)
        parent_link = img_tag.find_parent('a')
        if parent_link or img_tag.find_parent('button'):
            role_info['is_functional'] = True
            if parent_link:
                role_info['link_text'] = parent_link.get_text(strip=True)
                role_info['link_url'] = parent_link.get('href', '')

        # Check for and extract caption
        figure_parent = img_tag.find_parent('figure')
        if figure_parent:
            figcaption = figure_parent.find('figcaption')
            if figcaption:
                role_info['has_caption'] = True
                role_info['caption_text'] = figcaption.get_text(strip=True)

        # Check location context
        role_info['in_header'] = bool(img_tag.find_parent('header'))
        role_info['in_navigation'] = bool(img_tag.find_parent('nav'))
        role_info['in_content'] = bool(img_tag.find_parent(['article', 'main', 'section']))

        # If not decorative or functional, it's informative
        if not (role_info['is_decorative'] or role_info['is_functional']):
            role_info['is_informative'] = True

        return role_info

    def extract_image_info(self, html_content: str) -> List[Dict]:
        """Extract images and their context from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        images_data = []
        
        for img in soup.find_all('img'):
            # Get the full role info first
            role_info = self._determine_image_role(img)
            
            # Start with essential fields
            image_data = {
                'src': img.get('src', ''),
                'existing_alt': img.get('alt', ''),
                'role': 'decorative' if role_info['is_decorative'] else 
                       'functional' if role_info['is_functional'] else 
                       'informative',
                'context': self._get_surrounding_text(img)
            }
            
            # Only add title if it exists and is not empty
            title = img.get('title', '').strip()
            if title:
                image_data['title'] = title
            
            # Only add caption if it exists and is not empty
            if role_info['caption_text'].strip():
                image_data['caption'] = role_info['caption_text']
            
            # Add link info only for functional images with actual link text
            if role_info['is_functional'] and role_info.get('link_text', '').strip():
                image_data['link'] = {
                    'text': role_info['link_text'],
                    'url': role_info.get('link_url', '')
                }
            
            # Generate new alt text based on collected information
            role_info_for_generation = role_info  # Keep full role info for generation
            image_data_for_generation = image_data.copy()
            image_data_for_generation['role'] = role_info_for_generation
            image_data['suggested_alt'] = self.generate_alt_text(image_data_for_generation)
            
            images_data.append(image_data)
            
        return images_data

    def process_url(self, url: str) -> List[Dict]:
        """Process a URL and extract image information with context."""
        try:
            html_content = self.fetch_page_content(url)
            return self.extract_image_info(html_content)
        except Exception as e:
            raise Exception(f"Error processing URL: {str(e)}")

    def generate_alt_text(self, image_data: Dict) -> str:
        """
        Generate appropriate alt text using Claude based on image context and WCAG guidelines.
        """
        # Decorative images should have empty alt text
        if image_data['role']['is_decorative']:
            return ""
        
        context_info = {
            'role': 'functional' if image_data['role']['is_functional'] else 'informative',
            'existing_alt': image_data['existing_alt'],
            'title': image_data.get('title', ''),
            'caption': image_data['role'].get('caption_text', ''),
            'surrounding_text': {
                'before': image_data['context']['before'],
                'after': image_data['context']['after']
            }
        }

        # Special handling for functional images (in links/buttons)
        if image_data['role']['is_functional']:
            link_text = image_data['role'].get('link_text', '')
            link_url = image_data['role'].get('link_url', '')
            context_info['link'] = {'text': link_text, 'url': link_url}

        prompt = f"""Given this image context, generate appropriate WCAG 2.1-compliant alt text:

Image Role: {context_info['role']}
Existing Alt: {context_info['existing_alt']}
Title: {context_info['title']}
Caption: {context_info['caption']}
Link Info: {context_info.get('link', 'Not a link')}
Surrounding Text:
- Before: {context_info['surrounding_text']['before']}
- After: {context_info['surrounding_text']['after']}

Generate alt text following these WCAG guidelines:
1. If functional (in link/button), describe the action
2. Be concise but descriptive
3. Don't repeat information already visible in surrounding text
4. Don't use phrases like "image of" or "picture of"
5. Focus on the purpose and meaning of the image
6. Keep it under 125 characters when possible

Alt text:"""

        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract the content from the response
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating alt text: {str(e)}"

    def save_to_json(self, data: List[Dict], url: str) -> str:
        """
        Save image analysis results to a JSON file.
        Returns the filename of the saved JSON.
        """
        import json
        from datetime import datetime
        import os

        # Create 'output' directory if it doesn't exist
        if not os.path.exists('output'):
            os.makedirs('output')

        # Create filename based on URL and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_')
        filename = f'output/image_analysis_{safe_url}_{timestamp}.json'

        # Prepare the full report
        report = {
            'url': url,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_images': len(data),
            'images': data
        }

        # Save to JSON file with nice formatting
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filename

# Test the implementation
if __name__ == "__main__":
    generator = WCAGAltTextGenerator()
    try:
        url = "https://www.thecounselingpalette.com/post/board-games-for-couples"
        print("Fetching images from website...")
        results = generator.process_url(url)
        
        print(f"\nFound {len(results)} images!")
        
        # Save results to JSON file
        json_file = generator.save_to_json(results, url)
        print(f"Results saved to: {json_file}")
        
        # Print results to console
        for i, img in enumerate(results, 1):
            print(f"\nImage #{i}:")
            print(f"Source: {img['src']}")
            print(f"Current alt text: {img['existing_alt']}")
            print(f"Suggested alt text: {img['suggested_alt']}")
            
            if 'title' in img:
                print(f"Title: {img['title']}")
                
            if 'caption' in img:
                print(f"Caption: {img['caption']}")
            
            print(f"Role: {img['role']}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {str(e)}")