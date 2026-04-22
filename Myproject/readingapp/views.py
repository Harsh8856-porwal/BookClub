from django.shortcuts import render, redirect
from .models import Book
from django.http import JsonResponse
from django.contrib import messages

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login as auth_login, logout
import re
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import PyPDF2
from io import BytesIO
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text[:10000]  # Limit to first 10000 chars for better processing


def summarize_book_text(text):
    """Create a simple summary from book text"""
    if not text or len(text.strip()) < 100:
        return "This book appears to be too short or the text could not be extracted properly."

    # Clean and process text
    text = text.replace('\n', ' ').replace('\r', ' ')
    sentences = [s.strip() for s in text.split('.') if s.strip()]

    # Basic summarization logic
    word_count = len(text.split())
    char_count = len(text)

    # Try to extract first meaningful paragraph
    paragraphs = text.split('\n\n')
    first_paragraph = ""
    for para in paragraphs:
        if len(para.strip()) > 100:  # Meaningful paragraph
            first_paragraph = para.strip()[:500] + "..."
            break

    # Create summary
    summary = f"This book contains approximately {word_count:,} words ({char_count:,} characters). "

    if first_paragraph:
        summary += f"\n\nOpening excerpt: {first_paragraph}"

    # Try to identify potential themes or topics (basic keyword extraction)
    common_words = ['love', 'death', 'life', 'war', 'peace', 'family', 'friend', 'journey', 'adventure', 'mystery']
    found_themes = []
    text_lower = text.lower()
    for theme in common_words:
        if theme in text_lower:
            found_themes.append(theme.title())

    if found_themes:
        summary += f"\n\nPotential themes: {', '.join(found_themes[:5])}"

    return summary

  

def fetch_book_api_results(query, max_results=6):
    if not query:
        return []

    api_url = "https://openlibrary.org/search.json?" + urlencode({'q': query, 'limit': max_results})
    try:
        request = Request(api_url, headers={'User-Agent': 'BookClub/1.0'})
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
    except Exception:
        return []

    results = []
    for doc in data.get('docs', [])[:max_results]:
        title = doc.get('title') or 'Unknown Title'
        author_list = doc.get('author_name', [])
        author = ' & '.join(author_list) if author_list else 'Unknown Author'
        cover_id = doc.get('cover_i')
        cover = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
        results.append({
            'title': title,
            'author': author,
            'year': doc.get('first_publish_year'),
            'cover': cover,
            'source': 'OpenLibrary',
        })
    return results


def homepage(request):
    search_query = request.GET.get('search', '').strip()
    queryset = Book.objects.all().order_by('-id')

    if search_query:
        queryset = queryset.filter(
            book_name__icontains=search_query
        )

    queryset = queryset[:6].values()
    api_results = fetch_book_api_results(search_query) if search_query else []

    context = {
        'viewbook': queryset,
        'api_results': api_results,
        'search_query': search_query,
    }
    return render(request, 'readingapp/homepage.html', context)

   
def show(request):
    user = Book.objects.all().values()
    return render(request, "readingapp/bookdata.html", {'users': user})


def register(request):
    if request.method == "POST" and 'submit' in request.POST:
        user = Book(
            username=request.POST.get('unm'),
            email=request.POST.get('ue'),
            book_name=request.POST.get('bn'),
            author_name=request.POST.get('an'),
            book_category=request.POST.get('bcat'),
            book_chapter=request.POST.get('cn'),
            book_pages=request.POST.get('pn'),
            book_agegroup=request.POST.get('ag'),
            book_img=request.FILES.get('bfile'),
            book_file=request.FILES.get('bpdf')
        )
        user.save()

    return render(request, "home.html")

@login_required(login_url="/login")

def addbook(request):

    category = request.GET.get('category')

    if category and category != "All":
        viewbook = Book.objects.filter(book_category=category)
    else:
        viewbook = Book.objects.all()

    if request.method == "POST":

        email = request.POST.get('email')
        username = request.POST.get('username')
        book_name = request.POST.get('book_name')
        author_name = request.POST.get('author_name')
        book_chapter = request.POST.get('book_chapter')
        book_category = request.POST.get('book_category')
        book_pages = request.POST.get('book_pages')
        book_agegroup=request.POST.get('book_agegroup')

        book_file = request.FILES.get('book_file')
        book_img = request.FILES.get('book_img')

        Book.objects.create(
            email=email,
            username=username,
            book_name=book_name,
            author_name=author_name,
            book_chapter=book_chapter,
            book_category=book_category,
            book_pages=book_pages,
            book_agegroup=book_agegroup,
            book_file=book_file,
            book_img=book_img
        )

        return redirect('/addbook/')

    context = {'viewbook':viewbook}
    return render(request,'readingapp/addbook.html',context)


def category_books(request, category):
    # Check if category is age group (Kids/Young/Adult)
    if category in ['Kids', 'Young', 'Adult']:
        books = Book.objects.filter(book_agegroup__iexact=category)
    else:
        books = Book.objects.filter(book_category__iexact=category)

    context = {
        'books': books,
        'category': category
    }

    return render(request, 'readingapp/category_books.html', context)


def book_details(request, book_id):
    try:
        book = Book.objects.get(id=book_id)

        # Get similar books using the improved function
        similar_books = get_similar_books(book, limit=4)

        context = {
            'book': book,
            'similar_books': similar_books
        }

        return render(request, 'readingapp/book_details.html', context)

    except Book.DoesNotExist:
        return redirect('/')


def deletebook(request, id):
    query = Book.objects.get(id=id)
    query.delete()
    return redirect('/addbook')


def get_similar_books(current_book, limit=4):
    """Get similar books based on category and age group"""
    similar_books = []

    # First, get books from the same category
    category_books = Book.objects.filter(
        book_category=current_book.book_category
    ).exclude(id=current_book.id)[:limit//2]
    similar_books.extend(list(category_books))

    # Then, get books from the same age group
    remaining_slots = limit - len(similar_books)
    if remaining_slots > 0:
        age_books = Book.objects.filter(
            book_agegroup=current_book.book_agegroup
        ).exclude(id=current_book.id).exclude(
            id__in=[b.id for b in similar_books]
        )[:remaining_slots]
        similar_books.extend(list(age_books))

    # If still not enough, include some other books
    if len(similar_books) < limit:
        remaining_slots = limit - len(similar_books)
        other_books = Book.objects.exclude(
            id=current_book.id
        ).exclude(
            id__in=[b.id for b in similar_books]
        )[:remaining_slots]
        similar_books.extend(list(other_books))

    return similar_books[:limit]


def get_word_meaning(word, lang='en'):
    dictionary = {
        'ephemeral': {'en': 'lasting for a very short time', 'hi': 'क्षणिक'},
        'ubiquitous': {'en': 'found everywhere', 'hi': 'सर्वव्यापी'},
        'quaint': {'en': 'charmingly old-fashioned', 'hi': 'मनोरम'},
        'intricate': {'en': 'very complicated or detailed', 'hi': 'जटिल'},
        'ambiguous': {'en': 'open to more than one interpretation', 'hi': 'अस्पष्ट'},
        'eloquent': {'en': 'expressing yourself clearly and effectively', 'hi': 'बोली में प्रगतिशील'},
        'candid': {'en': 'honest and straightforward', 'hi': 'ईमानदार'},
    }
    return dictionary.get(word.lower(), {}).get(lang)


def find_book_in_query(query_text):
    if not query_text:
        return None

    name_search = re.search(r'"([^"]+)"', query_text)
    if name_search:
        return Book.objects.filter(book_name__icontains=name_search.group(1).strip()).first()

    title_patterns = [
        r'summary of ([\w\s]+)',
        r'tell me about ([\w\s]+)',
        r'about ([\w\s]+)',
        r'details of ([\w\s]+)',
        r'what is ([\w\s]+)',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, query_text)
        if match:
            text = match.group(1).strip()
            book = Book.objects.filter(book_name__icontains=text).first()
            if book:
                return book

    return Book.objects.filter(book_name__icontains=query_text).first()


def format_book_summary(book):
    summary_lines = [
        f"{book.book_name} by {book.author_name}",
        f"Category: {book.book_category}",
        f"Age group: {book.book_agegroup}",
        f"Pages: {book.book_pages}",
        f"Chapters: {book.book_chapter}",
    ]
    if book.book_file:
        summary_lines.append("PDF is available to read in the library.")
    if book.book_img:
        summary_lines.append("Cover image is available for this book.")
    return "\n".join(summary_lines)


def generate_chat_response(query, image_file=None, book_file=None):
    query_text = query.strip().lower() if query else ''
    referenced_book = find_book_in_query(query_text)

    if book_file:
        text = extract_text_from_pdf(book_file)
        if not text.strip():
            return "Could not extract text from the uploaded book. Please ensure it's a valid PDF with readable text."

        summary = summarize_book_text(text)
        recommendations = Book.objects.exclude(book_file__isnull=True)[:3]
        response = f"📚 Book analysis complete!\n\n{summary}\n\n"
        if recommendations:
            response += "📖 Recommended books from the library:\n"
            for book in recommendations:
                response += f"• {book.book_name} by {book.author_name} ({book.book_category}) - {book.book_agegroup}\n"
        return response

    if image_file:
        info_parts = [
            f"I received your image: {image_file.name}.",
        ]
        if hasattr(image_file, 'size'):
            info_parts.append(f"Image size: {image_file.size} bytes.")
        if 'cover' in query_text or 'book' in query_text or 'describe' in query_text:
            info_parts.append("It looks like a book cover image, and I can help describe the book details or genre.")
        else:
            info_parts.append("Ask questions like 'Describe this book cover' or 'What genre is this?'")
        return ' '.join(info_parts)

    if referenced_book and any(term in query_text for term in ['summary', 'about', 'describe', 'details', 'what is']):
        response = f"📘 {format_book_summary(referenced_book)}\n\n"
        similar = get_similar_books(referenced_book, limit=3)
        if similar:
            response += "📚 Similar books you may like:\n"
            for book in similar:
                response += f"• {book.book_name} by {book.author_name} ({book.book_category}) - {book.book_agegroup}\n"
        return response

    if 'summary' in query_text:
        title_match = re.search(r'summary of ([\w\s]+)', query_text)
        if title_match:
            title = title_match.group(1).strip()
            book = Book.objects.filter(book_name__icontains=title).first()
            if book:
                similar = get_similar_books(book, limit=3)
                response = (
                    f"Summary of '{book.book_name}' by {book.author_name}:\n"
                    f"This {book.book_category} book has {book.book_pages} pages and {book.book_chapter} chapters. "
                    f"It is ideal for {book.book_agegroup or 'all readers'} and explores themes common to {book.book_category} literature.\n"
                )
                if similar:
                    response += "\nRecommended similar books:\n"
                    for item in similar:
                        response += f"• {item.book_name} by {item.author_name} ({item.book_category}) - {item.book_agegroup}\n"
                return response
            return "I couldn't find that book in the library. Please provide a more specific title or try another book."
        return "Please tell me which book you want a summary for, for example: 'Summary of Pride and Prejudice'."

    if 'recommend' in query_text or 'suggest' in query_text or 'similar' in query_text:
        category = None
        if 'mystery' in query_text:
            category = 'Mystery'
        elif 'romantic' in query_text or 'love' in query_text:
            category = 'Romantic'
        elif 'spiritual' in query_text or 'inspiration' in query_text:
            category = 'Spiritual'
        elif 'fiction' in query_text:
            category = 'Fiction'
        elif 'adventure' in query_text or 'travel' in query_text:
            category = 'Adventure'
        elif 'classic' in query_text:
            category = 'Classic'

        if referenced_book and 'similar' in query_text:
            suggestions = get_similar_books(referenced_book, limit=3)
        elif category:
            suggestions = Book.objects.filter(book_category__iexact=category)[:3]
        else:
            suggestions = Book.objects.all()[:3]

        if suggestions:
            response_lines = ["Here are some books you may like:"]
            for book in suggestions:
                response_lines.append(f"• {book.book_name} by {book.author_name} ({book.book_category}) - {book.book_agegroup}")
            return '\n'.join(response_lines)
        return "I couldn't find a matching book recommendation right now. Try a different category or describe what you're looking for."

    if 'meaning' in query_text or 'translate' in query_text:
        lang = 'en'
        if 'hindi' in query_text:
            lang = 'hi'
        word_match = re.search(r'meaning of ([a-zA-Z]+)', query_text)
        if not word_match:
            word_match = re.search(r'translate ([a-zA-Z]+)', query_text)
        if word_match:
            word = word_match.group(1)
            meaning = get_word_meaning(word, lang)
            if meaning:
                return f"The meaning of '{word}' in {'Hindi' if lang=='hi' else 'English'} is: {meaning}."
            return f"I don't have the exact meaning for '{word}' yet, but I can help with other words."
        return "Please ask like 'Meaning of ephemeral in Hindi' or 'Translate ubiquitous'."

    return (
        "Hello! I'm your BookClub Assistant. I can help with:\n"
        "• Book summaries from our library\n"
        "• Book recommendations by category\n"
        "• Word meanings and translations\n"
        "• Image descriptions\n"
        "• PDF book analysis\n\n"
        "Try asking: 'Recommend mystery books', 'Summary of [book name]', or 'Meaning of intricate in Hindi'."
    )


def chat(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        image_file = request.FILES.get('image')
        book_file = request.FILES.get('book_file')
        response_text = generate_chat_response(query, image_file, book_file)
        return JsonResponse({'response': response_text})
    return redirect('/')


def login(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not email or not password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'readingapp/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another or login.')
            return render(request, 'readingapp/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered. Please login instead.')
            return render(request, 'readingapp/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        auth_login(request, user)
        messages.success(request, 'Account created and logged in successfully.')
        return redirect('/addbook')

    return render(request, 'readingapp/register.html')

def login1(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/addbook')
        messages.error(request, 'Invalid username or password.')
        return render(request, 'readingapp/login.html')

    return render(request, 'readingapp/login.html')

def logout1(request):
    logout(request)
    return redirect('/login')
def vision(request):
    return render(request, "readingapp/vision.html")

def blog(request):
    return render(request, "readingapp/blog.html")

def volunteer(request):
    return render(request, "readingapp/volunteer.html")

def tc(request):
    return render(request, "readingapp/T&C.html")