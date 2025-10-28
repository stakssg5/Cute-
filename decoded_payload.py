from faker import Faker
import random
import time
import os
from datetime import datetime
from colorama import Fore, Back, Style, init
from cryptography.fernet import Fernet
import base64
import hashlib
import requests

# Initialize colorama for Windows compatibility
init(autoreset=True)

class DatabaseInjector:
    def __init__(self):
        self.fake = Faker()
        self.output_file = f"injected_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.generated_count = 0
        self.encryption_key = None
        self.cipher_suite = None

    def generate_card_number(self):
        """Generate a random 16-digit card number"""
        return self.fake.credit_card_number()

    def generate_expiry_date(self):
        """Generate random expiry date (MM/YY format)"""
        expiry_date = self.fake.credit_card_expire()
        month = expiry_date.split('/')[0]
        year = expiry_date.split('/')[1]
        return month, year

    def generate_cvv(self):
        """Generate random 3-digit CVV"""
        return self.fake.credit_card_security_code()

    def generate_address(self):
        """Generate random address"""
        return self.fake.address().replace('\n', ', ')

    def generate_phone(self):
        """Generate random phone number"""
        return self.fake.phone_number()

    def generate_email(self):
        """Generate random email address with realistic domains"""
        # List of realistic email domains
        domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
            "icloud.com", "protonmail.com", "live.com", "msn.com", "comcast.net",
            "verizon.net", "att.net", "sbcglobal.net", "bellsouth.net", "cox.net",
            "charter.net", "earthlink.net", "juno.com", "netzero.net", "roadrunner.com"
        ]
        
        # Generate first and last name
        first_name = self.fake.first_name().lower()
        last_name = self.fake.last_name().lower()
        
        # Sometimes add numbers or random characters
        if random.choice([True, False]):
            suffix = random.randint(1, 999)
            username = f"{first_name}.{last_name}{suffix}"
        else:
            username = f"{first_name}.{last_name}"
        
        # Choose random domain
        domain = random.choice(domains)
        
        return f"{username}@{domain}"

    def setup_encryption(self, key):
        """Setup encryption with the provided key"""
        # Convert the key to bytes and create a Fernet key
        key_bytes = key.encode('utf-8')
        # Pad or truncate to 32 bytes for Fernet
        key_bytes = key_bytes.ljust(32, b'0')[:32]
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.cipher_suite = Fernet(fernet_key)
        self.encryption_key = key

    def encrypt_data(self, data):
        """Encrypt the data using the encryption key"""
        if self.cipher_suite is None:
            raise ValueError("Encryption not initialized. Call setup_encryption first.")
        return self.cipher_suite.encrypt(data.encode('utf-8'))

    def fetch_key_from_server(self):
        """Fetch key from remote server"""
        try:
            print(f"{Fore.CYAN}[FETCH]{Style.RESET_ALL} Connecting to key server...")
            url = "http://encrypt.techifytechnicalstaff.site/key.txt"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            server_key = response.text.strip()
            print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Key fetched successfully!")
            return server_key
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to fetch key: {e}")
            return "5c8dbce60589acf2b4beddb0c6386298"
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Key fetch error: {e}")
            return "5c8dbce60589acf2b4beddb0c6386298"

    def process_server_key(self, server_key):
        """Process key from server"""
        try:
            print(f"{Fore.MAGENTA}[PROCESS]{Style.RESET_ALL} Processing server key...")
            
            # Expected key from server
            expected_key = "5c8dbce60589acf2b4beddb0c6386298"
            
            if server_key == expected_key:
                # This key corresponds to "Aflatoon@123"
                processed_key = "Aflatoon@123"
                print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Key processed successfully!")
                return processed_key
            else:
                print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Key mismatch! Using fallback...")
                return "Aflatoon@123"
                
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Key processing failed: {e}")
            return "Aflatoon@123"

    def get_encryption_key(self):
        """Get encryption key from remote server"""
        print(f"{Fore.YELLOW}[SECURITY]{Style.RESET_ALL} Fetching key from server...")
        
        # Fetch key from server
        server_key = self.fetch_key_from_server()
        
        # Process the key
        encryption_key = self.process_server_key(server_key)
        
        print(f"{Fore.YELLOW}[SECURITY]{Style.RESET_ALL} Using key: {Fore.CYAN}***{Style.RESET_ALL}")
        return encryption_key

    def show_sql_messages(self):
        """Display realistic SQL injection messages with colors"""
        messages = [
            ("[INFO]", "Connecting to database server...", Fore.CYAN),
            ("[INFO]", "Database connection established", Fore.GREEN),
            ("[SQL]", "Executing SQL injection query...", Fore.YELLOW),
            ("[AUTH]", "Bypassing authentication...", Fore.RED),
            ("[TABLE]", "Accessing user records table...", Fore.MAGENTA),
            ("[EXTRACT]", "Extracting sensitive data...", Fore.BLUE),
            ("[PARSE]", "Parsing database response...", Fore.CYAN),
            ("[SUCCESS]", "Data extraction successful", Fore.GREEN),
            ("[PREP]", "Preparing data for output...", Fore.YELLOW),
            ("[WRITE]", "Writing to local file...", Fore.BLUE)
        ]
        
        for prefix, message, color in messages:
            print(f"{color}{prefix}{Style.RESET_ALL} {message}")
            time.sleep(random.uniform(0.3, 0.8))

    def generate_person_details(self):
        """Generate complete person details in the specified format"""
        card_number = self.generate_card_number()
        month, year = self.generate_expiry_date()
        cvv = self.generate_cvv()
        address = self.generate_address()
        phone = self.generate_phone()
        email = self.generate_email()
        
        return f"{card_number}|{month}|{year}|{cvv}|{address}|{phone}|{email}"

    def save_to_file(self, data):
        """Save generated data to text file (encrypted)"""
        # Encrypt the data before saving
        encrypted_data = self.encrypt_data(data)
        with open(self.output_file, 'ab') as f:
            f.write(encrypted_data + b'\n')

    def show_loading_animation(self, duration=2):
        """Show a loading animation"""
        chars = "|/-\\"
        end_time = time.time() + duration
        while time.time() < end_time:
            for char in chars:
                print(f"\r{Fore.YELLOW}[LOADING] {char}{Style.RESET_ALL}", end="", flush=True)
                time.sleep(0.1)
        print(f"\r{Fore.GREEN}[READY] {' ' * 20}{Style.RESET_ALL}")

    def validate_key(self):
        """Validate key before proceeding with any operations"""
        print(f"{Fore.YELLOW}[AUTH]{Style.RESET_ALL} Please enter your access key:")
        user_key = input(f"{Fore.CYAN}[INPUT]{Style.RESET_ALL} Key: ").strip()
        
        if user_key == "Aflatoon@123":
            print(f"{Fore.GREEN}[AUTH]{Style.RESET_ALL} Key validation successful!")
            print(f"{Fore.GREEN}[AUTH]{Style.RESET_ALL} Access granted to proceed!")
            return True
        else:
            print(f"{Fore.RED}[AUTH]{Style.RESET_ALL} Key validation failed!")
            print(f"{Fore.RED}[AUTH]{Style.RESET_ALL} Access denied!")
            return False

    def inject_data(self, count=2):
        """Main injection process with beautiful colors"""
        # Header with colors
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Back.WHITE} D3Vl Dumps Generator 1.0 {Style.RESET_ALL}")
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print()
        
        # FIRST: Validate key before proceeding
        if not self.validate_key():
            print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.RED}[ACCESS DENIED]{Style.RESET_ALL} Invalid key! Cannot proceed.")
            print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[ACCESS GRANTED]{Style.RESET_ALL} Key validated! Proceeding with injection...")
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print()
        
        print(f"{Fore.CYAN}[INIT]{Style.RESET_ALL} Starting database injection sequence...")
        self.show_loading_animation(2)
        
        print(f"{Fore.MAGENTA}[TARGET]{Style.RESET_ALL} Injecting {Fore.YELLOW}{count}{Style.RESET_ALL} user records...")
        print()
        
        # Generate cards first (without encryption)
        generated_cards = []
        for i in range(count):
            self.generated_count += 1
            
            print(f"{Fore.BLUE}[INJECT]{Style.RESET_ALL} Processing record {Fore.YELLOW}#{self.generated_count}{Style.RESET_ALL}...")
            self.show_sql_messages()
            
            # Generate the actual data
            person_data = self.generate_person_details()
            generated_cards.append(person_data)
            
            print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Data extracted: {Fore.WHITE}{Back.GREEN}{person_data}{Style.RESET_ALL}")
            print()
            
            # Wait before next injection
            if i < count - 1:  # Don't wait after the last one
                wait_time = random.uniform(2, 5)
                print(f"{Fore.YELLOW}[WAIT]{Style.RESET_ALL} Waiting {Fore.CYAN}{wait_time:.1f}s{Style.RESET_ALL} before next injection...")
                self.show_loading_animation(wait_time)
                print()
        
        # Now setup encryption with validated key
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[SECURITY]{Style.RESET_ALL} Cards generated! Now setting up encryption...")
        print()
        
        # Setup encryption with user's key
        print(f"{Fore.CYAN}[SECURITY]{Style.RESET_ALL} Setting up encryption...")
        self.setup_encryption("Aflatoon@123")
        print(f"{Fore.GREEN}[ENCRYPTED]{Style.RESET_ALL} Data will be encrypted with AES-256 encryption!")
        print()
        
        # Encrypt and save the generated cards
        print(f"{Fore.MAGENTA}[ENCRYPT]{Style.RESET_ALL} Encrypting generated cards...")
        for i, card_data in enumerate(generated_cards, 1):
            print(f"{Fore.BLUE}[ENCRYPT]{Style.RESET_ALL} Encrypting card {Fore.YELLOW}#{i}{Style.RESET_ALL}...")
            self.save_to_file(card_data)
            print(f"{Fore.GREEN}[SAVED]{Style.RESET_ALL} Card {i} encrypted and saved!")
        
        # Completion message with colors
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[COMPLETE]{Style.RESET_ALL} Injection sequence finished!")
        print(f"{Fore.BLUE}[OUTPUT]{Style.RESET_ALL} {Fore.YELLOW}{self.generated_count}{Style.RESET_ALL} records saved to: {Fore.CYAN}{self.output_file}{Style.RESET_ALL}")
        print(f"{Fore.RED}{'=' * 60}{Style.RESET_ALL}")

def main():
    """Main function to run the database injector"""
    injector = DatabaseInjector()
    
    try:
        # Generate 2 records by default
        injector.inject_data(2)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[ABORT]{Style.RESET_ALL} Injection sequence interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Injection failed: {Fore.RED}{e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
