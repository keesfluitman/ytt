#!/usr/bin/env python3
"""
Quick API test script for YTT backend
Run with: python test_api.py
"""

import httpx
import asyncio
from rich.console import Console
from rich.table import Table

console = Console()

# Change this if your server is on a different port
BASE_URL = "http://localhost:8001"


async def test_health():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        return response.status_code == 200, response.json()


async def test_languages():
    """Test supported languages endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/languages")
        return response.status_code == 200, response.json()


async def test_providers():
    """Test providers endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/providers")
        return response.status_code == 200, response.json()


async def test_detect_language():
    """Test language detection"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/translate/detect",
            data={"text": "Bonjour le monde"}
        )
        return response.status_code == 200, response.json()


async def test_translate():
    """Test translation endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/translate",
            data={
                "text": "Hallo Welt! Wie geht es dir?",
                "source_lang": "de",
                "target_lang": "en"
            }
        )
        return response.status_code == 200, response.json()


async def test_history():
    """Test history endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/history")
        return response.status_code == 200, response.json()


async def test_youtube_extract_id():
    """Test YouTube ID extraction"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/youtube/extract-id",
            params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        return response.status_code == 200, response.json()


async def test_youtube_info():
    """Test YouTube video info (requires yt-dlp)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/youtube/info",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "use_cookies": "none"
            }
        )
        # This might fail if yt-dlp has issues, so we check for 200 or 500
        return response.status_code in [200, 500], response.json() if response.status_code == 200 else {"error": response.text[:100]}


async def run_all_tests():
    """Run all tests and display results"""
    console.print("\n[bold cyan]🧪 Testing YTT API Endpoints[/bold cyan]\n")
    
    # Create results table
    table = Table(title="Test Results")
    table.add_column("Endpoint", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Response", style="dim")
    
    tests = [
        ("Health Check", "/health", test_health),
        ("Get Languages", "/api/languages", test_languages),
        ("Get Providers", "/api/providers", test_providers),
        ("Detect Language", "/api/translate/detect", test_detect_language),
        ("Translate Text", "/api/translate", test_translate),
        ("Get History", "/api/history", test_history),
        ("YouTube Extract ID", "/api/youtube/extract-id", test_youtube_extract_id),
        ("YouTube Video Info", "/api/youtube/info", test_youtube_info),
    ]
    
    for test_name, endpoint, test_func in tests:
        try:
            success, response = await test_func()
            if success:
                status = "[green]✓ PASS[/green]"
                # Truncate response for display
                resp_str = str(response)[:80] + "..." if len(str(response)) > 80 else str(response)
            else:
                status = "[red]✗ FAIL[/red]"
                resp_str = str(response)
            
            table.add_row(test_name, status, resp_str)
            
        except Exception as e:
            table.add_row(test_name, "[red]✗ ERROR[/red]", f"[red]{str(e)[:80]}[/red]")
    
    console.print(table)
    console.print("\n[bold]LibreTranslate URL:[/bold]", BASE_URL.replace("8001", "5000").replace("localhost", "192.168.1.249"))


async def test_youtube_fetch():
    """Test fetching YouTube transcript (this might take a while)"""
    console.print("\n[bold cyan]🎬 Testing YouTube Transcript Fetch[/bold cyan]\n")
    console.print("[yellow]This might take 10-30 seconds...[/yellow]\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/youtube/fetch",
            json={
                "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Short "Me at the zoo" video
                "source_lang": "en",
                "use_cookies": "none"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            console.print("[green]✓ YouTube transcript fetch successful![/green]")
            console.print(f"Video: {result.get('title', 'Unknown')}")
            if result.get('source_transcript'):
                transcript_preview = result['source_transcript'][:200] + "..."
                console.print(f"Transcript preview: {transcript_preview}")
        else:
            console.print(f"[red]✗ YouTube fetch failed: {response.status_code}[/red]")
            console.print(response.text[:500])


async def test_with_file():
    """Test file upload translation"""
    console.print("\n[bold cyan]📄 Testing File Upload[/bold cyan]\n")
    
    # Create a test file
    test_content = "Dies ist ein Test. Ich hoffe, es funktioniert gut!"
    
    async with httpx.AsyncClient() as client:
        files = {
            'file': ('test.txt', test_content.encode(), 'text/plain')
        }
        data = {
            'source_lang': 'de',
            'target_lang': 'en'
        }
        
        response = await client.post(
            f"{BASE_URL}/api/translate",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            console.print("[green]✓ File upload successful![/green]")
            console.print(f"Original: {result['original_text']}")
            console.print(f"Translated: {result['translated_text']}")
        else:
            console.print(f"[red]✗ File upload failed: {response.status_code}[/red]")
            console.print(response.text)


if __name__ == "__main__":
    # Check if server is running
    console.print(f"[yellow]Testing API at {BASE_URL}...[/yellow]\n")
    
    try:
        # Run basic tests
        asyncio.run(run_all_tests())
        
        # Optional: Test file upload
        # asyncio.run(test_with_file())
        
        # Optional: Test YouTube fetch (takes longer)
        # asyncio.run(test_youtube_fetch())
        
    except httpx.ConnectError:
        console.print(f"[red]❌ Cannot connect to server at {BASE_URL}[/red]")
        console.print("Make sure the server is running with: [cyan]./run_dev.sh[/cyan]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")