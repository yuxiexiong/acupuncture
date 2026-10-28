const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('/Users/ruizhixu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const sharp = require('/Users/ruizhixu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');

(async () => {
  const out = path.join(__dirname, 'qa');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({headless: true, executablePath: '/Users/ruizhixu/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'});
  const page = await browser.newPage({viewport: {width: 1440, height: 900}, deviceScaleFactor: 1});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  const count = await page.evaluate(() => window.slideDeck.count);
  const layouts = [];
  for (let i = 0; i < count; i++) {
    await page.evaluate(i => window.slideDeck.show(i), i);
    await page.locator('.slide.active img').evaluateAll(imgs => Promise.all(imgs.map(img => img.decode())));
    layouts.push(await page.locator('.slide.active').evaluate(slide => {
      const footer = slide.querySelector('footer').getBoundingClientRect();
      const children = [...slide.querySelector('.content').children];
      return {
        title: slide.dataset.title,
        footerOverlap: children.filter(el => el.getBoundingClientRect().bottom > footer.top - 8).map(el => el.tagName + ':' + (el.textContent || el.getAttribute('alt') || '').slice(0,60)),
        imagesLoaded: [...slide.querySelectorAll('img')].every(img => img.complete && img.naturalWidth > 0)
      };
    }));
    await page.locator('#deck').screenshot({path: path.join(out, `slide-${String(i+1).padStart(2,'0')}.png`)});
  }
  await page.keyboard.press('Home');
  await page.keyboard.press('ArrowRight');
  const keyboardNext = await page.locator('#counter').textContent();
  await page.keyboard.press('End');
  const keyboardEnd = await page.locator('#counter').textContent();
  await page.keyboard.press('n');
  const notesOpen = await page.locator('#notes').evaluate(el => el.open && el.querySelector('p').textContent.length > 0);
  await page.keyboard.press('Escape');
  await page.keyboard.press('o');
  const tocCount = await page.locator('#toc-items button').count();
  await page.locator('#toc-items button').nth(3).click();
  const tocNavigation = await page.locator('#counter').textContent();
  const links = await page.locator('a').evaluateAll(as => [...new Set(as.map(a => a.href))]);
  const brokenLinks = links.filter(url => url.startsWith('file://') && !fs.existsSync(decodeURIComponent(new URL(url).pathname)));
  const externalDependencies = await page.locator('script[src],link[href],img[src]').evaluateAll(es => es.map(e => e.src || e.href).filter(s => /^https?:/.test(s)));
  await page.setViewportSize({width: 390, height: 844});
  await page.evaluate(() => window.slideDeck.show(0));
  await page.screenshot({path: path.join(out, 'mobile.png')});
  const mobileFits = await page.locator('#deck').evaluate(el => { const r=el.getBoundingClientRect(); return r.left>=-1 && r.right<=innerWidth+1 && r.top>=-1 && r.bottom<=innerHeight-55; });
  const thumbs = await Promise.all(Array.from({length: count}, async (_,i) => ({input: await sharp(path.join(out, `slide-${String(i+1).padStart(2,'0')}.png`)).resize(480,270).png().toBuffer(), left:(i%4)*480, top:Math.floor(i/4)*270})));
  await sharp({create:{width:1920,height:Math.ceil(count/4)*270,channels:3,background:'#ffffff'}}).composite(thumbs).png().toFile(path.join(out, 'contact-sheet.png'));
  const htmlSha256 = crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'index.html'))).digest('hex');
  const passed = count === 16 && layouts.every(s => s.imagesLoaded && s.footerOverlap.length === 0) && errors.length === 0 && keyboardNext === '2 / 16' && keyboardEnd === '16 / 16' && notesOpen && tocCount === 16 && tocNavigation === '4 / 16' && brokenLinks.length === 0 && externalDependencies.length === 0 && mobileFits;
  const report = {passed,htmlSha256,verifiedUtc:new Date().toISOString(),count,layouts,errors,keyboardNext,keyboardEnd,notesOpen,tocCount,tocNavigation,brokenLinks,externalDependencies,mobileFits};
  fs.writeFileSync(path.join(out, 'validation.json'), JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
  await browser.close();
  if (!passed) process.exitCode = 1;
})().catch(e => { console.error(e); process.exit(1); });
