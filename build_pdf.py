import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import time
import re

LESSON_URLS = [
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/0-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/0-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/1-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/1-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/1-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/1-4",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-4",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-5",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/2-6",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/3-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/3-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/3-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/3-4",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/4-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/4-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/4-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/5-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/5-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/5-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d1/6-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/1-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/2-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/2-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/2-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/3-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/3-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/3-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/3-4",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/3-5",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/4-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/5-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/5-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/5-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/5-4",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/6-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/6-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d2/7-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/1-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/2-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/2-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/3-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/4-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/4-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/4-3",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/5-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/5-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/6-1",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/6-2",
    "https://multicampus-claudecode.code-serendipity.com/lesson/d3/7-1",
]

def clean_text(text):
    """Clean and normalize text for PDF output."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    # Remove non-latin1 characters that fpdf can't handle, keeping common chars
    result = []
    for ch in text:
        try:
            ch.encode('latin-1')
            result.append(ch)
        except UnicodeEncodeError:
            result.append('?')
    return ''.join(result)

def fetch_lesson(url):
    """Fetch and parse a lesson page."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove nav/sidebar/footer elements
        for el in soup.select('nav, aside, footer, header, script, style, button'):
            el.decompose()

        # Try to get main content area
        main = soup.select_one('main, article, .content, [class*="lesson"], [class*="content"]')
        if not main:
            main = soup.body

        if not main:
            return {'title': url, 'content': '(내용 없음)'}

        # Extract title
        title_el = main.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else url.split('/')[-1]

        # Extract structured content
        blocks = []
        for el in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'pre', 'code', 'blockquote']):
            tag = el.name
            text = el.get_text(separator=' ', strip=True)
            if text:
                blocks.append((tag, text))

        return {'title': title, 'url': url, 'blocks': blocks}
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return {'title': url, 'url': url, 'blocks': [('p', f'(오류: {e})')]}


class CoursePDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, 'Claude Code Workshop - Full Course Notes', align='R')
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def build_pdf(lessons, output_path):
    pdf = CoursePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)

    # Cover page
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(30, 30, 30)
    pdf.ln(40)
    pdf.cell(0, 20, 'Claude Code Workshop', align='C')
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 12, 'Full Course Notes', align='C')
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 10, 'Day 1 ~ Day 3 | All Lessons', align='C')
    pdf.ln(8)
    pdf.cell(0, 10, 'https://multicampus-claudecode.code-serendipity.com', align='C')

    for i, lesson in enumerate(lessons, 1):
        pdf.add_page()
        url = lesson.get('url', '')
        title = lesson.get('title', '')
        blocks = lesson.get('blocks', [])

        # URL breadcrumb
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(150, 150, 150)
        short_url = url.replace('https://multicampus-claudecode.code-serendipity.com', '')
        pdf.cell(0, 6, clean_text(f'({i}/{len(lessons)}) {short_url}'))
        pdf.ln(2)

        # Lesson title (h1)
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(0, 10, clean_text(title))
        pdf.ln(4)

        # Separator
        pdf.set_draw_color(220, 50, 50)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 90, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(6)

        W = pdf.w - pdf.l_margin - pdf.r_margin  # effective width

        for tag, text in blocks:
            cleaned = clean_text(text)
            if not cleaned:
                continue
            pdf.set_x(pdf.l_margin)  # always reset x

            if tag == 'h1':
                continue  # already printed as title
            elif tag == 'h2':
                pdf.set_font('Helvetica', 'B', 14)
                pdf.set_text_color(30, 30, 120)
                pdf.ln(3)
                pdf.multi_cell(W, 8, cleaned)
                pdf.ln(2)
            elif tag == 'h3':
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(50, 100, 150)
                pdf.ln(2)
                pdf.multi_cell(W, 7, cleaned)
                pdf.ln(1)
            elif tag == 'h4':
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(70, 70, 70)
                pdf.multi_cell(W, 7, cleaned)
            elif tag in ('pre', 'code'):
                pdf.set_font('Courier', '', 9)
                pdf.set_text_color(40, 40, 40)
                pdf.set_fill_color(240, 240, 240)
                pdf.multi_cell(W, 5, cleaned, fill=True)
                pdf.ln(2)
            elif tag == 'li':
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(W, 6, '  - ' + cleaned)
            elif tag == 'blockquote':
                pdf.set_font('Helvetica', 'I', 10)
                pdf.set_text_color(80, 80, 80)
                pdf.set_fill_color(248, 248, 248)
                pdf.multi_cell(W, 6, '  ' + cleaned, fill=True)
                pdf.ln(1)
            else:  # p
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(W, 6, cleaned)
                pdf.ln(2)

    pdf.output(output_path)
    print(f"\nPDF saved: {output_path} ({pdf.page_no()} pages)")


if __name__ == '__main__':
    lessons = []
    for i, url in enumerate(LESSON_URLS, 1):
        print(f"[{i}/{len(LESSON_URLS)}] Fetching: {url}")
        lesson = fetch_lesson(url)
        lessons.append(lesson)
        time.sleep(0.3)

    output = r'C:\Users\student\Documents\mcp_test\claude_code_workshop_full.pdf'
    build_pdf(lessons, output)
