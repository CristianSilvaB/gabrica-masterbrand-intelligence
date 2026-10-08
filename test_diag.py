import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        # Mobile Android Pixel user agent and viewport
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            viewport={'width': 412, 'height': 915},
            is_mobile=True,
            has_touch=True,
            locale='es-CO'
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        url = "https://www.google.com/maps/place/Agrocampo/@4.6615186,-74.0622493,17z/data=!3m1!4b1!4m6!3m5!1s0x8e3f9a597c02f60f:0xf0f3b494469c19c9!8m2!3d4.6615186!4d-74.0622493!16s%2Fg%2F1v8324k1"
        print("Navigating with mobile context...")
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_timeout(4000)
        
        await page.screenshot(path="mobile_view.png")
        print("Saved mobile_view.png")
        print("Title:", await page.title())
        print("URL:", page.url)
        
        # Check buttons and tabs
        btns = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('button, a, [role="tab"]')).map(el => ({
                text: el.innerText ? el.innerText.trim() : '',
                aria: el.getAttribute('aria-label')
            })).filter(x => x.text.includes('opin') || x.text.includes('Opin') || (x.aria && x.aria.includes('opin')));
        }''')
        print("Mobile opinion buttons:", btns)
        
        await browser.close()

asyncio.run(inspect())
