import time
import random
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib.parse import urljoin, urlparse

class EnhancedWebScraper:
    def __init__(self):
        self.driver = None
        
    def setup_selenium_driver(self):
        """Setup Selenium WebDriver with enhanced anti-detection"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Add random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/115.0.1901.200 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Add language preference
        chrome_options.add_argument('--lang=en-US,en;q=0.9')
        
        # Disable automation flags
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })
            
            # Mask WebDriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            print(f"Selenium setup failed: {e}")
            return False
    
    def handle_alibaba_page(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[BeautifulSoup]]:
        """Special handling for Alibaba pages with enhanced anti-detection"""
        try:
            # Set longer timeouts for Alibaba
            self.driver.set_page_load_timeout(40)
            self.driver.set_script_timeout(30)
            
            # Clear all cookies and cache
            self.driver.delete_all_cookies()
            self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            
            # Additional anti-detection measures
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'DNT': '1',
                }
            })
            
            # Load the page
            print("Loading Alibaba page...")
            self.driver.get(url)
            
            # Wait for page load with multiple conditions
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda d: d.execute_script("""
                        return document.readyState === 'complete' && 
                        document.querySelector('.product-title, .title, .product-name') !== null
                    """)
                )
            except:
                print("Waiting for basic page load...")
            
            # Scroll through the page slowly
            print("Scrolling through page...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(0, last_height, 200):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.1)
            
            # Wait for dynamic content
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            # Try to find and click interactive elements
            print("Looking for interactive elements...")
            buttons_to_try = [
                "//button[contains(., 'Show More')]",
                "//div[contains(., 'Show More')]",
                "//span[contains(., 'Show More')]",
                "//a[contains(., 'Contact')]",
                "//button[contains(., 'Contact')]",
                "//div[contains(@class, 'contact')]",
                "//button[contains(@class, 'show-more')]",
                "//button[contains(@class, 'next-btn')]",
                "//span[contains(., 'View details')]",
                "//a[contains(@class, 'more')]"
            ]
            
            for xpath in buttons_to_try:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                except:
                    continue
            
            # Get content after interactions
            text = self.driver.execute_script("return document.body.innerText;")
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            return text, html, soup
            
        except Exception as e:
            print(f"Alibaba page handling error: {e}")
            return None, None, None
    
    def scrape_with_selenium(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[BeautifulSoup]]:
        """Enhanced Selenium scraping with better JavaScript handling"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Initialize driver if needed
                if not self.driver:
                    if not self.setup_selenium_driver():
                        return None, None, None
                
                # Clear cookies and set timeouts
                self.driver.delete_all_cookies()
                self.driver.set_page_load_timeout(20)
                self.driver.set_script_timeout(20)
                
                # Load the page
                print(f"Loading URL: {url}")
                self.driver.get(url)
                
                # Wait for page load
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Handle dynamic content loading
                try:
                    # Scroll to middle
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(0.5)
                    
                    # Scroll to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                    
                    # Back to top
                    self.driver.execute_script("window.scrollTo(0, 0);")
                except Exception as e:
                    print(f"Scroll error (non-critical): {e}")
                
                # Click contact buttons
                contact_buttons = [
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contact')]",
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show')]",
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contact')]"
                ]
                
                clicked_buttons = set()
                for button_xpath in contact_buttons:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, button_xpath)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled() and button not in clicked_buttons:
                                try:
                                    button.click()
                                    clicked_buttons.add(button)
                                    time.sleep(0.3)
                                except:
                                    continue
                    except:
                        continue
                
                # Extract content
                try:
                    # Get text content
                    text = self.driver.execute_script("""
                        return Array.from(document.body.getElementsByTagName('*'))
                            .map(el => el.textContent)
                            .join(' ')
                            .replace(/\\s+/g, ' ')
                            .trim();
                    """)
                    
                    # Get HTML content
                    html_content = self.driver.execute_script("return document.documentElement.outerHTML;")
                    
                    # Parse HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    return text, html_content, soup
                    
                except Exception as e:
                    print(f"Content extraction error: {e}")
                    retry_count += 1
                    continue
                
            except Exception as e:
                print(f"Selenium scraping error: {e}")
                retry_count += 1
                time.sleep(1)
        
        return None, None, None

    def extract_alibaba_product(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product details specifically from Alibaba"""
        details = {
            'title': '',
            'price': '',
            'description': '',
            'specifications': {},
            'features': [],
            'images': [],
            'brand': '',
            'model': '',
            'supplier': '',
            'min_order': '',
            'availability': '',
            'shipping': '',
            'payment_terms': ''
        }
        
        # Title
        title_selectors = [
            'h1.module-pdp-title', '.title', 'h1.product-title',
            '.product-name', '[data-spm-anchor-id*="title"]'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                details['title'] = title_elem.get_text().strip()
                break
        
        # Price
        price_selectors = [
            '.price', '.product-price', '[data-spm-anchor-id*="price"]',
            '.ma-reference-price', '.ma-spec-price', '.ma-price-promotion'
        ]
        price_texts = []
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems:
                price_text = elem.get_text().strip()
                if price_text and any(c.isdigit() for c in price_text):
                    price_texts.append(price_text)
        if price_texts:
            details['price'] = ' | '.join(price_texts)
        
        # Description
        desc_selectors = [
            '.product-description', '.description', '#J-rich-text-description',
            '[data-spm-anchor-id*="description"]'
        ]
        desc_texts = []
        for selector in desc_selectors:
            elems = soup.select(selector)
            for elem in elems:
                desc_text = elem.get_text().strip()
                if desc_text:
                    desc_texts.append(desc_text)
        if desc_texts:
            details['description'] = '\n'.join(desc_texts)
        
        # Specifications
        spec_selectors = [
            '.product-attributes', '.specifications', 
            'table.ma-spec-table tr', '.ma-specification'
        ]
        for selector in spec_selectors:
            rows = soup.select(selector)
            for row in rows:
                try:
                    # Try to find key-value pairs
                    key_elem = row.select_one('th, td:first-child, .attr-name')
                    val_elem = row.select_one('td:last-child, .attr-value')
                    
                    if key_elem and val_elem:
                        key = key_elem.get_text().strip()
                        val = val_elem.get_text().strip()
                        if key and val:
                            details['specifications'][key] = val
                except:
                    continue
        
        # Images
        img_selectors = [
            '.main-image img', '.thumb-image img', '.detail-image img',
            '[data-spm-anchor-id*="image"] img'
        ]
        for selector in img_selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src', '')
                if src and not src.startswith('data:'):
                    if '50x50' in src:  # Replace thumbnail with full image
                        src = src.replace('50x50', '800x800')
                    details['images'].append(urljoin(url, src))
        
        # Supplier
        supplier_selectors = [
            '.company-name', '.supplier-name', '[data-spm-anchor-id*="supplier"]',
            '.company-info-name'
        ]
        for selector in supplier_selectors:
            elem = soup.select_one(selector)
            if elem:
                details['supplier'] = elem.get_text().strip()
                break
        
        # Min Order
        min_order_selectors = [
            '.min-order', '.moq', '[data-spm-anchor-id*="moq"]'
        ]
        for selector in min_order_selectors:
            elem = soup.select_one(selector)
            if elem:
                details['min_order'] = elem.get_text().strip()
                break
        
        return details
    
    def extract_product_details(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract detailed product information"""
        # Use Alibaba-specific extraction for Alibaba URLs
        if 'alibaba.com' in url:
            return self.extract_alibaba_product(soup, url)
        details = {
            'title': '',
            'price': '',
            'description': '',
            'specifications': {},
            'features': [],
            'images': [],
            'brand': '',
            'model': '',
            'supplier': '',
            'min_order': '',
            'availability': '',
            'rating': '',
            'reviews_count': ''
        }
        
        # Product title
        title_selectors = [
            'h1.product-title', 'h1.title', 'h1.product-name',
            'div.product-title', '.product-name', '[data-testid="product-title"]'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                details['title'] = title_elem.get_text().strip()
                break
                
        # Price
        price_selectors = [
            '.product-price', '.price', '[data-testid="product-price"]',
            '.offer-price', '.sale-price', '.current-price'
        ]
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                details['price'] = price_elem.get_text().strip()
                break
                
        # Description
        desc_selectors = [
            '.product-description', '.description', '#description',
            '[data-testid="product-description"]', '.detail-desc'
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                details['description'] = desc_elem.get_text().strip()
                break
                
        # Specifications/Features
        spec_selectors = [
            '.specifications', '.specs', '.product-specs',
            '.product-attributes', '.features', '.product-features'
        ]
        for selector in spec_selectors:
            specs = soup.select(f"{selector} li, {selector} tr")
            for spec in specs:
                text = spec.get_text().strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    details['specifications'][key.strip()] = value.strip()
                else:
                    details['features'].append(text)
                    
        # Images
        img_selectors = [
            '.product-images img', '.gallery img', '.product-gallery img',
            '[data-testid="product-image"] img', '.product-thumb img'
        ]
        for selector in img_selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src', '')
                if src and not src.startswith('data:'):
                    details['images'].append(urljoin(url, src))
                    
        # Brand/Manufacturer
        brand_selectors = [
            '.brand', '.manufacturer', '[data-testid="product-brand"]',
            '.product-brand', '.vendor'
        ]
        for selector in brand_selectors:
            brand_elem = soup.select_one(selector)
            if brand_elem:
                details['brand'] = brand_elem.get_text().strip()
                break
                
        # Model/SKU
        model_selectors = [
            '.model', '.sku', '[data-testid="product-model"]',
            '.product-sku', '.item-code'
        ]
        for selector in model_selectors:
            model_elem = soup.select_one(selector)
            if model_elem:
                details['model'] = model_elem.get_text().strip()
                break
                
        # Supplier/Seller
        supplier_selectors = [
            '.supplier', '.seller', '[data-testid="seller-info"]',
            '.vendor-info', '.store-name'
        ]
        for selector in supplier_selectors:
            supplier_elem = soup.select_one(selector)
            if supplier_elem:
                details['supplier'] = supplier_elem.get_text().strip()
                break
                
        # Minimum Order
        min_order_selectors = [
            '.min-order', '.moq', '[data-testid="min-order"]',
            '.minimum-order', '.min-quantity'
        ]
        for selector in min_order_selectors:
            min_order_elem = soup.select_one(selector)
            if min_order_elem:
                details['min_order'] = min_order_elem.get_text().strip()
                break
                
        return details
        
    def extract_contact_info(self, text: str, html_content: str = "", url: str = "") -> Dict:
        """Extract contact information from text and HTML with improved phone detection"""
        contacts = {
            'emails': set(),
            'phones': set(),
            'whatsapp': set(),
            'website_url': url,
            'social_media': {}
        }
        
        if not text or not html_content:
            return contacts
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Email extraction from text and href
        email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}')
        
        # Find emails in text
        emails = email_pattern.findall(text)
        contacts['emails'].update(email for email in emails if self.validate_email(email))
        
        # Find emails in href attributes
        for link in soup.find_all('a', href=True):
            if 'mailto:' in link['href']:
                email = link['href'].replace('mailto:', '').split('?')[0]
                if self.validate_email(email):
                    contacts['emails'].add(email)
        
        # Phone extraction with improved patterns
        phone_patterns = [
            r'(?:Phone|Tel|Telephone|Contact|Call)(?:[:\s])*([+\d\s\-()]{10,20})',  # Phone: +1234567890
            r'[\+]?[\d]{1,3}[-\s]?[\d]{3,4}[-\s]?[\d]{3,4}[-\s]?[\d]{3,4}',  # International format
            r'\b[\d]{3}[-\s]?[\d]{3}[-\s]?[\d]{4}\b',  # US format
            r'\+?[\d]{10,14}',  # Plain numbers
            r'(?:WhatsApp|Whatsapp|WA)(?:[:\s])*([+\d\s\-()]{10,20})'  # WhatsApp numbers
        ]
        
        # Search in both text and HTML
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                phone = match.group(1) if len(match.groups()) > 0 else match.group(0)
                cleaned = self.clean_phone_number(phone)
                if self.validate_phone_number(cleaned):
                    if 'whatsapp' in pattern.lower():
                        contacts['whatsapp'].add(cleaned)
                    else:
                        contacts['phones'].add(cleaned)
        
        # Look for phone numbers in specific HTML elements
        phone_elements = soup.find_all(['a', 'span', 'div', 'p'], text=re.compile(r'(?:Phone|Tel|Call|Contact|WhatsApp|Mobile).*'))
        for element in phone_elements:
            text_content = element.get_text()
            for pattern in phone_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    phone = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    cleaned = self.clean_phone_number(phone)
                    if self.validate_phone_number(cleaned):
                        if 'whatsapp' in pattern.lower():
                            contacts['whatsapp'].add(cleaned)
                        else:
                            contacts['phones'].add(cleaned)
        
        # Look for tel: links
        for link in soup.find_all('a', href=True):
            if 'tel:' in link['href']:
                phone = link['href'].replace('tel:', '')
                cleaned = self.clean_phone_number(phone)
                if self.validate_phone_number(cleaned):
                    contacts['phones'].add(cleaned)
        
        # Convert sets to lists for JSON serialization
        contacts['emails'] = list(contacts['emails'])
        contacts['phones'] = list(contacts['phones'])
        contacts['whatsapp'] = list(contacts['whatsapp'])
        
        return contacts
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) < 5:
            return False
        pattern = r'^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(pattern, email))
    
    def clean_phone_number(self, phone: str) -> str:
        """Clean phone number"""
        if not phone:
            return ""
        # Keep only digits, +, and spaces
        cleaned = re.sub(r'[^\d+\s]', '', phone.strip())
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def validate_phone_number(self, phone: str) -> bool:
        """Validate phone number"""
        if not phone:
            return False
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Basic length check
        if not (7 <= len(digits) <= 15):
            return False
            
        # Skip obviously invalid patterns
        invalid_patterns = [
            r'^0+$',  # All zeros
            r'^1+$',  # All ones
            r'^\d{5,}0+$',  # Long number ending in zeros
            r'^(\d)\1{5,}$',  # Same digit repeated too many times
            r'^\d{4,}$'  # Likely to be an ID or product number
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, digits):
                return False
        
        # Check for common phone number patterns
        valid_patterns = [
            r'^\+?1\d{10}$',  # US/Canada: +1 followed by 10 digits
            r'^\+?[2-9]\d{9,14}$',  # International: + followed by 10-15 digits
            r'^0[1-9]\d{8,10}$',  # Local numbers starting with 0
            r'^[1-9]\d{7,11}$'  # Generic 8-12 digit numbers
        ]
        
        return any(re.match(pattern, digits) for pattern in valid_patterns)
    
    def close(self):
        """Close browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

def save_to_csv(data: List[Dict], filename: str = None) -> str:
    """Save scraped data to CSV file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"scraped_data_{timestamp}.csv"
    
    if not filename.lower().endswith('.csv'):
        filename += '.csv'
    
    # Flatten the nested dictionaries for CSV
    flattened_data = []
    for item in data:
        flat_item = {
            'URL': item.get('url', ''),
            'Title': item.get('product_details', {}).get('title', ''),
            'Price': item.get('product_details', {}).get('price', ''),
            'Description': item.get('product_details', {}).get('description', ''),
            'Brand': item.get('product_details', {}).get('brand', ''),
            'Model': item.get('product_details', {}).get('model', ''),
            'Supplier': item.get('product_details', {}).get('supplier', ''),
            'Min_Order': item.get('product_details', {}).get('min_order', ''),
            'Images': ', '.join(item.get('product_details', {}).get('images', [])),
            'Emails': ', '.join(item.get('contacts', {}).get('emails', [])),
            'Phones': ', '.join(item.get('contacts', {}).get('phones', [])),
            'WhatsApp': ', '.join(item.get('contacts', {}).get('whatsapp', [])),
            'Specifications': str(item.get('product_details', {}).get('specifications', {})),
            'Features': ', '.join(item.get('product_details', {}).get('features', []))
        }
        flattened_data.append(flat_item)
    
    df = pd.DataFrame(flattened_data)
    df.to_csv(filename, index=False, encoding='utf-8')
    return filename

def main():
    scraper = EnhancedWebScraper()
    all_data = []
    
    try:
        while True:
            print("\n1. Scrape single URL")
            print("2. Scrape multiple URLs from file")
            print("3. Exit")
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                url = input("\nEnter URL to scrape: ").strip()
                if url:
                    print(f"\nScraping {url}...")
                    
                    # Initialize the driver if needed
                    if not scraper.driver:
                        print("Setting up browser...")
                        scraper.setup_selenium_driver()
                    
                    # Use specialized handling for Alibaba
                    if 'alibaba.com' in url:
                        print("Detected Alibaba URL - Using specialized scraper...")
                        text, html, soup = scraper.handle_alibaba_page(url)
                    else:
                        text, html, soup = scraper.scrape_with_selenium(url)
                    
                    if text and soup:
                        print("Extracting information...")
                        # Extract contacts and product details
                        contacts = scraper.extract_contact_info(text, html, url)
                        product_details = scraper.extract_product_details(soup, url)
                        
                        # Store the data
                        data = {
                            'url': url,
                            'contacts': contacts,
                            'product_details': product_details,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        all_data.append(data)
                        
                        # Print summary
                        print("\nFound information:")
                        print(f"Title: {product_details['title']}")
                        print(f"Price: {product_details['price']}")
                        print(f"Brand: {product_details['brand']}")
                        print(f"Emails: {contacts['emails']}")
                        print(f"Phones: {contacts['phones']}")
                        print(f"WhatsApp: {contacts['whatsapp']}")
                        
                        # Save to CSV after each successful scrape
                        if all_data:
                            filename = save_to_csv(all_data)
                            print(f"\nData saved to: {filename}")
                    else:
                        print("Failed to scrape the page.")
                        
            elif choice == "2":
                filename = input("\nEnter file name with URLs (one per line): ").strip()
                try:
                    with open(filename, 'r') as f:
                        urls = [line.strip() for line in f if line.strip()]
                    
                    for url in urls:
                        print(f"\nScraping {url}...")
                        text, html, soup = scraper.scrape_with_selenium(url)
                        if text and soup:
                            contacts = scraper.extract_contact_info(text, html, url)
                            product_details = scraper.extract_product_details(soup, url)
                            
                            data = {
                                'url': url,
                                'contacts': contacts,
                                'product_details': product_details,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            all_data.append(data)
                            
                            print("✓ Successfully scraped")
                        else:
                            print("✗ Failed to scrape")
                        
                        time.sleep(random.uniform(1, 3))  # Random delay between requests
                    
                    # Save all data to CSV
                    if all_data:
                        filename = save_to_csv(all_data)
                        print(f"\nAll data saved to: {filename}")
                        
                except FileNotFoundError:
                    print(f"File not found: {filename}")
                except Exception as e:
                    print(f"Error reading file: {e}")
                    
            elif choice == "3":
                break
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if all_data:
            try:
                filename = save_to_csv(all_data)
                print(f"\nData saved to: {filename}")
            except Exception as e:
                print(f"Error saving data: {e}")
        scraper.close()

if __name__ == "__main__":
    main()
