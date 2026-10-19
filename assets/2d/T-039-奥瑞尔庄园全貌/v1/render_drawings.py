"""Export the editable SVG sources beside this script, preserving A2 scale."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
import fitz

parser = argparse.ArgumentParser(description='Render PNG previews; PDF is opt-in.')
parser.add_argument('--pdf', action='store_true')
args = parser.parse_args()
folder = Path(__file__).resolve().parent
order = ['manor_总平面', 'manor_平面_一楼', 'manor_平面_二楼', 'manor_剖面']
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
    page = browser.new_page(viewport={'width':3564, 'height':2520}, device_scale_factor=1)
    for name in order:
        svg = (folder/(name+'.svg')).read_text()
        page.set_content('<html><head><style>@page{size:594mm 420mm;margin:0}html,body{margin:0}svg{display:block;width:100vw;height:100vh}@media print{svg{width:594mm;height:420mm}}</style></head><body>'+svg+'</body></html>')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(folder/(name+'.png')))
        if args.pdf:
            page.pdf(path=str(folder/(name+'.pdf')), width='594mm',height='420mm',print_background=True,prefer_css_page_size=True)
    browser.close()
if args.pdf:
    combined = fitz.open()
    for name in order:
        with fitz.open(folder/(name+'.pdf')) as doc:
            assert len(doc) == 1
            combined.insert_pdf(doc)
    combined.save(folder/'manor_设计图集-v1.pdf')
print('4 PNG previews exported; PDF only with --pdf.')
