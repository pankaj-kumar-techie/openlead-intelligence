# OpenLead Intelligence - Selenium-based Scraper

"""
Selenium-based scraper for JavaScript-heavy websites.
Provides browser automation capabilities for dynamic content.
"""

import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

from config import settings
from utils.logger import get_logger
from models.schemas import Company, ScrapingResult, DataSource

logger = get_logger(__name__)


class SeleniumScraper:
    """
    Selenium-based scraper for dynamic websites.
    
    Use this for sites that require JavaScript execution or
    have anti-bot protection that blocks simple HTTP requests.
    """
    
    def __init__(
        self,
        headless: bool = None,
        timeout: int = None,
        source: DataSource = DataSource.OTHER
    ):
        """
        Initialize Selenium scraper.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
            source: Data source identifier
        """
        self.headless = headless if headless is not None else settings.headless_browser
        self.timeout = timeout if timeout is not None else settings.browser_timeout
        self.source = source
        self.driver = None
        
        logger.info("Initializing Selenium scraper")
    
    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Common options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Anti-detection options
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            user_agent = settings.get_headers()['User-Agent']
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            # Execute script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error("Make sure Chrome and ChromeDriver are installed")
            raise
    
    def get_page(self, url: str, wait_for: Optional[str] = None, wait_time: int = 10) -> bool:
        """
        Load a page and optionally wait for an element.
        
        Args:
            url: URL to load
            wait_for: CSS selector to wait for (optional)
            wait_time: Maximum wait time in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._init_driver()
            
            logger.info(f"Loading page: {url}")
            self.driver.get(url)
            
            if wait_for:
                logger.debug(f"Waiting for element: {wait_for}")
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
            
            return True
            
        except TimeoutException:
            logger.error(f"Timeout waiting for page or element: {url}")
            return False
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            return False
    
    def scroll_to_bottom(self, pause_time: float = 1.0, max_scrolls: int = 10):
        """
        Scroll to bottom of page to load dynamic content.
        
        Args:
            pause_time: Pause between scrolls in seconds
            max_scrolls: Maximum number of scroll attempts
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            
            while scrolls < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time)
                
                # Calculate new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                
                last_height = new_height
                scrolls += 1
            
            logger.debug(f"Scrolled {scrolls} times")
            
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
    
    def find_elements(self, selector: str, by: By = By.CSS_SELECTOR) -> List:
        """
        Find elements by selector.
        
        Args:
            selector: Element selector
            by: Selector type (CSS_SELECTOR, XPATH, etc.)
        
        Returns:
            List of WebElements
        """
        try:
            return self.driver.find_elements(by, selector)
        except Exception as e:
            logger.error(f"Error finding elements with selector '{selector}': {e}")
            return []
    
    def find_element(self, selector: str, by: By = By.CSS_SELECTOR):
        """
        Find single element by selector.
        
        Args:
            selector: Element selector
            by: Selector type
        
        Returns:
            WebElement or None
        """
        try:
            return self.driver.find_element(by, selector)
        except Exception as e:
            logger.debug(f"Element not found with selector '{selector}': {e}")
            return None
    
    def get_page_source(self) -> str:
        """Get current page source."""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return ""
    
    def take_screenshot(self, filepath: str):
        """
        Take screenshot of current page.
        
        Args:
            filepath: Path to save screenshot
        """
        try:
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved to: {filepath}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    def execute_script(self, script: str):
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
        
        Returns:
            Script return value
        """
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None
    
    def close(self):
        """Close browser and cleanup."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor."""
        self.close()


if __name__ == "__main__":
    print("Selenium Scraper")
    print("\nExample usage:")
    print("  with SeleniumScraper() as scraper:")
    print("      scraper.get_page('https://example.com')")
    print("      scraper.scroll_to_bottom()")
    print("      elements = scraper.find_elements('.company-card')")
    print("\nNote: Requires Chrome and ChromeDriver to be installed")
