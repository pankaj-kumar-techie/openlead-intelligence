# OpenLead Intelligence - Helper Utilities

"""
Common utility functions for the scraping framework.
Includes URL validation, domain extraction, retry decorators, and data cleaning.
"""

import re
import time
import validators
from functools import wraps
from typing import Optional, Callable, Any
from urllib.parse import urlparse, urljoin
import requests
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
    
    Returns:
        Domain name or None if invalid
    
    Examples:
        >>> extract_domain("https://www.example.com/path")
        'example.com'
        >>> extract_domain("http://subdomain.example.co.uk")
        'example.co.uk'
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return None


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return validators.url(url) is True


def normalize_url(url: str) -> str:
    """
    Normalize URL by adding protocol and removing trailing slashes.
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters (keep alphanumeric, spaces, and common punctuation)
    text = re.sub(r'[^\w\s\-.,!?()&]', '', text)
    
    return text.strip()


def clean_company_name(name: str) -> str:
    """
    Clean and normalize company name.
    
    Args:
        name: Company name
    
    Returns:
        Cleaned company name
    """
    if not name:
        return ""
    
    # Remove common suffixes
    suffixes = [
        r'\s+Inc\.?$', r'\s+LLC\.?$', r'\s+Ltd\.?$', r'\s+Limited$',
        r'\s+Corp\.?$', r'\s+Corporation$', r'\s+Co\.?$', r'\s+Company$',
        r'\s+GmbH$', r'\s+S\.A\.?$', r'\s+AG$', r'\s+PLC$'
    ]
    
    cleaned = name
    for suffix in suffixes:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
    
    # Clean text
    cleaned = clean_text(cleaned)
    
    return cleaned


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text.
    
    Args:
        text: Text containing email
    
    Returns:
        Email address or None
    """
    if not text:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text.
    
    Args:
        text: Text containing phone number
    
    Returns:
        Phone number or None
    """
    if not text:
        return None
    
    # Simple phone pattern (can be improved)
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
    match = re.search(phone_pattern, text)
    
    return match.group(0) if match else None


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry function on exception with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    
    Returns:
        Decorated function
    
    Example:
        @retry_on_exception(max_retries=3, delay=1.0, backoff=2.0)
        def fetch_data():
            return requests.get("https://example.com")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}: {e}"
                        )
            
            # Raise the last exception if all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def rate_limit(calls: int = 1, period: float = 1.0) -> Callable:
    """
    Decorator to rate limit function calls.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    
    Returns:
        Decorated function
    
    Example:
        @rate_limit(calls=10, period=60.0)  # 10 calls per minute
        def api_call():
            return requests.get("https://api.example.com")
    """
    min_interval = period / calls
    
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            
            return result
        
        return wrapper
    return decorator


def check_robots_txt(url: str, user_agent: str = "*") -> bool:
    """
    Check if URL is allowed by robots.txt.
    
    Args:
        url: URL to check
        user_agent: User agent string
    
    Returns:
        True if allowed, False otherwise
    """
    try:
        from urllib.robotparser import RobotFileParser
        
        domain = extract_domain(url)
        if not domain:
            return False
        
        robots_url = f"https://{domain}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        # If we can't check, assume it's allowed
        return True


def safe_get(dictionary: dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        dictionary: Dictionary to search
        *keys: Nested keys
        default: Default value if key not found
    
    Returns:
        Value or default
    
    Example:
        >>> data = {"a": {"b": {"c": 123}}}
        >>> safe_get(data, "a", "b", "c")
        123
        >>> safe_get(data, "a", "x", "y", default=0)
        0
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    
    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


if __name__ == "__main__":
    # Test utilities
    print("Testing URL utilities:")
    print(f"Domain: {extract_domain('https://www.example.com/path')}")
    print(f"Valid URL: {validate_url('https://example.com')}")
    print(f"Normalized: {normalize_url('example.com/')}")
    
    print("\nTesting text cleaning:")
    print(f"Clean text: {clean_text('  Hello   World!  ')}")
    print(f"Clean company: {clean_company_name('Example Inc.')}")
    
    print("\nTesting extraction:")
    print(f"Email: {extract_email('Contact us at info@example.com')}")
    print(f"Phone: {extract_phone('Call us at +1-234-567-8900')}")
